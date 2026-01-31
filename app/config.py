"""Конфигурация приложения.

Настройки берутся из переменных окружения через pydantic-settings.
Это даёт:
- строгую валидацию при старте (лучше упасть сразу, чем в середине работы),
- единый источник правды для сервисов (API и Telegram-бот),
- удобные дефолты для локальной разработки.

Принципы:
- все переменные имеют префикс NIGHTLIGHT_ (см. env_prefix),
- токен обязателен и должен быть достаточно длинным,
- для локалки можно использовать mock GPIO-бэкенд.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки времени выполнения, загружаемые из переменных окружения."""

    model_config = SettingsConfigDict(env_prefix="NIGHTLIGHT_", case_sensitive=False)

    api_token: str = Field(min_length=16)
    public_base_url: str = Field(
        default="https://localhost:8443",
        description=(
            "Публичный URL, который используют внешние клиенты "
            "(например, Telegram-бот)."
        ),
    )

    gpio_backend: str = Field(default="mock", description="'mock' или 'rpi'")
    led_gpio_pin: int = Field(default=18, ge=0)
    pwm_frequency_hz: int = Field(default=800, ge=1)

    ssl_certfile: str | None = Field(default=None)
    ssl_keyfile: str | None = Field(default=None)

    log_level: str = Field(default="INFO")

    telegram_bot_token: str | None = Field(default=None)
    telegram_allowed_chat_ids: str = Field(
        default="",
        description=(
            "Список разрешённых chat id через запятую для управления устройством."
        ),
    )
    telegram_api_url: str = Field(
        default="https://localhost:8443",
        description="Базовый URL API, который использует Telegram-бот.",
    )
    telegram_tls_verify: bool = Field(
        default=True,
        description="Проверять TLS-сертификат при вызовах API из Telegram-бота.",
    )

    device_id: str = Field(default="nightlight")

    def allowed_chat_ids(self) -> set[int]:
        """Разобрать список разрешённых идентификаторов чата из настроек."""

        value = self.telegram_allowed_chat_ids.strip()
        if not value:
            # Пустое значение => ограничение выключено (разрешено всем).
            return set()
        result: set[int] = set()
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            # Telegram chat_id — это int, поэтому приводим и собираем в set.
            result.add(int(part))
        return result
