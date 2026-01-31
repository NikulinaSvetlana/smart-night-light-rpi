"""Фабрика GPIO-бэкендов.

Задача модуля — по строковому имени бэкенда (“mock”, “rpi”) вернуть объект,
который реализует контракт PwmOutput.

Такой уровень абстракции нужен, чтобы остальной код не знал:
- как именно создаётся PWM,
- какие импорты нужны для реального железа,
- где находится mock-реализация.
"""

from __future__ import annotations

from .base import PwmOutput
from .mock_gpio import MockPwmOutput


def create_pwm_output(backend: str, *, pin: int, frequency_hz: int) -> PwmOutput:
    """Создать PWM-выход для выбранного бэкенда."""

    # Нормализуем строку, чтобы значения из env были более “прощающе” обработаны.
    backend_norm = backend.strip().lower()
    if backend_norm == "mock":
        # Mock не требует pin, поэтому он игнорируется.
        return MockPwmOutput(frequency_hz=frequency_hz)
    if backend_norm == "rpi":
        # Импортируем здесь, чтобы на не-RPi окружениях модуль не падал при импорте.
        from .rpi_gpio import RpiPwmOutput

        return RpiPwmOutput(pin=pin, frequency_hz=frequency_hz)

    # Если бэкенд неизвестен — это ошибка конфигурации, пусть сервис упадёт при старте.
    raise ValueError(f"Unsupported GPIO backend: {backend}")

