"""Фабрика приложения.

Этот модуль собирает FastAPI-приложение из “кусков”:
- конфигурации (Settings),
- доменного слоя (реестр устройств и сценариев),
- транспортного слоя (роуты API),
- веб-статики (простая HTML/JS страница),
- системных вещей (логирование, учёт времени старта, корректное закрытие ресурсов).

Почему “фабрика”:
- удобно создавать приложение по-разному для продакшена и тестов,
- можно подменять реестр/настройки в unit-тестах без глобальных синглтонов,
- точка сборки одна, и видно, что именно включено.

Ключевые функции:
- build_registry(): создаёт реестр устройств (сейчас одно LED-устройство),
- create_app(): создаёт FastAPI, вешает роутеры и middleware.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from app.config import Settings
from app.domain.devices import DeviceRegistry, LedDevice
from app.domain.scenarios import ScenarioRegistry
from app.gpio.factory import create_pwm_output
from app.gpio.led import LedController
from app.logging_config import configure_logging

from .routes_led import router as led_router
from .routes_scenarios import router as scenarios_router
from .routes_system import router as system_router
from .routes_web import router as web_router


def build_registry(settings: Settings) -> DeviceRegistry:
    """Собрать реестр по умолчанию с одним LED-устройством.

Здесь связываются настройки окружения и конкретная реализация “железа”:
- выбирается GPIO-бэкенд (mock/rpi),
- создаётся PWM-выход и контроллер,
- контроллер регистрируется как устройство в доменном реестре.
"""

    registry = DeviceRegistry()
    pwm = create_pwm_output(
        settings.gpio_backend,
        pin=settings.led_gpio_pin,
        frequency_hz=settings.pwm_frequency_hz,
    )
    controller = LedController(pwm=pwm)
    registry.register_led(
        LedDevice(device_id=settings.device_id, controller=controller)
    )
    return registry


def create_app(
    settings: Settings | None = None,
    registry: DeviceRegistry | None = None,
) -> FastAPI:
    """Создать приложение FastAPI.

Функция intentionally “толстая”: это место, где видно всю композицию сервиса.
Внутренние детали (GPIO, доменная логика) остаются в своих модулях, но wiring
делается здесь.
"""

    settings = settings or Settings()  # type: ignore[call-arg]
    configure_logging(settings.log_level)
    logger = logging.getLogger("nightlight")

    registry = registry or build_registry(settings)
    app = FastAPI(title="Nightlight", version="0.1.0")

    # Храним зависимости в app.state, чтобы:
    # - зависимости FastAPI могли доставать их через Request,
    # - тесты могли подменять их при создании приложения.
    app.state.settings = settings
    app.state.registry = registry
    app.state.scenarios = ScenarioRegistry()
    app.state.started_at = time.time()

    # Web UI лежит рядом с Python-пакетом (app/web) и раздаётся как статика.
    root = Path(__file__).resolve().parents[1]
    web_dir = root / "web"
    app.mount("/static", StaticFiles(directory=str(web_dir), html=False), name="static")

    app.include_router(web_router)
    app.include_router(system_router)
    app.include_router(led_router)
    app.include_router(scenarios_router)

    @app.middleware("http")
    async def _log_errors(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        try:
            return await call_next(request)
        except Exception:  # noqa: BLE001
            # Логируем любые необработанные ошибки единообразно, чтобы в логах
            # была хотя бы HTTP-операция и путь. Исключение пробрасываем дальше,
            # чтобы FastAPI сформировал корректный ответ/трейс.
            logging.getLogger("nightlight.error").exception(
                "Необработанная ошибка: %s %s", request.method, request.url.path
            )
            raise

    @app.on_event("shutdown")
    def _shutdown() -> None:
        # Закрываем GPIO-ресурсы и прочие “железные” вещи.
        logger.info("Завершение работы...")
        registry.close()

    return app

