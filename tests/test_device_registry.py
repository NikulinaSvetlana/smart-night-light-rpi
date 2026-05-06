"""Unit-тесты доменного реестра устройств.

Тут проверяется, что:
- реестр умеет регистрировать и возвращать устройства,
- список устройств формируется корректно,
- отсутствие устройства выражается через KeyError (а не через None),
  чтобы транспортный слой мог конвертировать это в 404.
"""

from __future__ import annotations

import pytest

from app.domain.devices import DeviceRegistry, LedDevice
from app.gpio.led import LedController
from app.gpio.mock_gpio import MockPwmOutput


def test_registry_register_and_get() -> None:
    """Регистрация устройства должна делать его доступным по device_id."""
    registry = DeviceRegistry()
    # В тестах используем моковый PWM, чтобы не зависеть от GPIO.
    led = LedController(pwm=MockPwmOutput(frequency_hz=800))
    registry.register_led(LedDevice(device_id="nightlight", controller=led))

    devices = registry.list_devices()
    assert len(devices) == 1
    assert devices[0].device_id == "nightlight"

    device = registry.get_led("nightlight")
    assert device.device_id == "nightlight"


def test_registry_missing_raises() -> None:
    """Если устройство отсутствует — ожидаем KeyError."""
    registry = DeviceRegistry()
    with pytest.raises(KeyError):
        registry.get_led("missing")
