"""GPIO-бэкенд через fake-rpi для разработки на обычном ПК.

Пакет fake-rpi предоставляет эмуляцию RPi.GPIO, позволяя запускать
проект без Raspberry Pi. В отличие от MockPwmOutput, здесь используется
«настоящий» API RPi.GPIO (setmode, setup, PWM), но через эмулятор.

Установка: pip install fake-rpi
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from threading import Lock

from .base import PwmOutput

logger = logging.getLogger("nightlight.gpio.fake_rpi")


@dataclass(slots=True)
class FakeRpiPwmOutput(PwmOutput):
    """PWM-выход через эмулятор fake-rpi."""

    pin: int
    frequency_hz: int
    _lock: Lock = field(init=False, repr=False)
    _gpio: object = field(init=False, repr=False)
    _pwm: object = field(init=False, repr=False)
    _started: bool = field(init=False, default=False)
    _duty_cycle: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self._lock = Lock()
        try:
            # fake-rpi.
            from fake_rpi.RPi import GPIO as gpio
        except ImportError as exc:
            raise RuntimeError(
                "fake-rpi не установлен. Установите: pip install fake-rpi"
            ) from exc

        gpio.setmode(gpio.BCM)
        gpio.setup(self.pin, gpio.OUT)
        self._gpio = gpio
        self._pwm = gpio.PWM(self.pin, self.frequency_hz)
        logger.info(
            "fake-rpi PWM: pin=%d, freq=%d Гц",
            self.pin,
            self.frequency_hz,
        )

    def start(self, duty_cycle_percent: float) -> None:
        with self._lock:
            self._pwm.start(float(duty_cycle_percent))  # type: ignore[union-attr]
            self._started = True
            self._duty_cycle = float(duty_cycle_percent)
            logger.debug("PWM start: duty=%.1f%%", duty_cycle_percent)

    def change_duty_cycle(self, duty_cycle_percent: float) -> None:
        with self._lock:
            if not self._started:
                self._pwm.start(float(duty_cycle_percent))  # type: ignore[union-attr]
                self._started = True
            else:
                self._pwm.ChangeDutyCycle(float(duty_cycle_percent))  # type: ignore[union-attr]
            self._duty_cycle = float(duty_cycle_percent)
            logger.debug("PWM duty: %.1f%%", duty_cycle_percent)

    def stop(self) -> None:
        with self._lock:
            if self._started:
                self._pwm.stop()  # type: ignore[union-attr]
                self._started = False
                self._duty_cycle = 0.0
                logger.debug("PWM stop")

    def close(self) -> None:
        self.stop()
        try:
            from fake_rpi.RPi import GPIO as gpio

            gpio.cleanup(self.pin)
        except Exception:  # noqa: BLE001
            pass
        logger.info("fake-rpi PWM closed: pin=%d", self.pin)
