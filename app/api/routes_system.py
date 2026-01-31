"""Системные эндпоинты: health, status и metrics.

Тут собраны “служебные” ручки:
- /health: простая проверка “процесс жив” (обычно без аутентификации),
- /status: расширенная диагностика (uptime, устройства, состояния),
- /metrics: минимальные метрики в формате Prometheus.

Зачем разделять /health и /status:
- /health должен быть максимально простым и быстрым,
- /status может делать больше работы и требовать токен.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Request, Response

from app.api.auth import AuthContext
from app.api.deps import get_auth, get_registry, get_settings
from app.api.schemas import DeviceInfoOut, LedStateOut, StatusOut
from app.config import Settings
from app.domain.devices import DeviceRegistry

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    """Проверка “сервис жив”.

Эндпоинт не требует токена, чтобы его можно было использовать для простых
проверок и мониторинга доступности.
"""
    return {"status": "ok"}


@router.get("/status", response_model=StatusOut)
def status_endpoint(
    request: Request,
    settings: Settings = Depends(get_settings),
    registry: DeviceRegistry = Depends(get_registry),
    _auth: AuthContext = Depends(get_auth),
) -> StatusOut:
    """Диагностический статус сервиса.

Возвращает:
- uptime,
- выбранный GPIO-бэкенд,
- список устройств,
- состояния LED-устройств.
"""
    now = time.time()
    started_at = float(getattr(request.app.state, "started_at", now))
    uptime = now - started_at

    # Получаем список устройств из доменного реестра и дополняем состояниями.
    devices = registry.list_devices()
    led_states: dict[str, LedStateOut] = {}
    for device in devices:
        if device.device_type != "led":
            continue
        state = registry.get_led(device.device_id).state()
        led_states[device.device_id] = LedStateOut(
            is_on=state.is_on, brightness=state.brightness
        )
    return StatusOut(
        service="nightlight",
        uptime_s=uptime,
        gpio_backend=settings.gpio_backend,
        devices=[
            DeviceInfoOut(device_id=d.device_id, device_type=d.device_type)
            for d in devices
        ],
        led_states=led_states,
    )


@router.get("/metrics", include_in_schema=False)
def metrics(
    registry: DeviceRegistry = Depends(get_registry),
    _auth: AuthContext = Depends(get_auth),
) -> Response:
    """Метрики в текстовом формате Prometheus.

Это максимально простой “экспортёр” без сторонних библиотек:
- nightlight_led_on{device_id="..."} 0|1
- nightlight_led_brightness{device_id="..."} 0.000000..1.000000
"""
    lines: list[str] = []
    for device in registry.list_devices():
        if device.device_type != "led":
            continue
        state = registry.get_led(device.device_id).state()
        lines.append(
            f'nightlight_led_on{{device_id="{device.device_id}"}} '
            f"{1 if state.is_on else 0}"
        )
        lines.append(
            f'nightlight_led_brightness{{device_id="{device.device_id}"}} '
            f"{state.brightness:.6f}"
        )
    body = "\n".join(lines) + ("\n" if lines else "")
    return Response(content=body, media_type="text/plain; version=0.0.4")

