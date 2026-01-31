"""GPIO-бэкенд Raspberry Pi через RPi.GPIO.

Этот модуль импортируется только при NIGHTLIGHT_GPIO_BACKEND=rpi.

Почему импорт “ленивый” (в factory.py):
- на обычном ПК модуля RPi.GPIO нет, и импорт упал бы сразу,
- при backend=mock мы вообще не хотим тянуть зависимости RPi.

Примечание по PWM:
- используется BCM-нумерация пинов,
- duty_cycle задаётся в процентах 0..100 (как в RPi.GPIO),
- cleanup(pin) вызывается при закрытии, чтобы освободить пин.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from .base import PwmOutput


class RpiGpioImportError(RuntimeError):
    """Выбрасывается, если модуль RPi.GPIO недоступен."""


@dataclass(slots=True)
class RpiPwmOutput(PwmOutput):
    """PWM-выход на базе RPi.GPIO PWM.

Класс инкапсулирует:
- конфигурацию пина,
- создание объекта PWM,
- безопасный доступ из разных потоков через lock.
"""

    pin: int
    frequency_hz: int
    _lock: Lock = field(init=False, repr=False)
    _gpio: Any = field(init=False, repr=False)
    _pwm: Any = field(init=False, repr=False)
    _started: bool = field(init=False, default=False, repr=False)

    def __post_init__(self) -> None:
        # Защищаем операции над GPIO, потому что FastAPI может обрабатывать
        # запросы параллельно.
        self._lock = Lock()
        try:
            import RPi.GPIO as gpio  # type: ignore[import-not-found]
        except Exception as exc:  # noqa: BLE001
            raise RpiGpioImportError(
                "RPi.GPIO недоступен. Установите его на Raspberry Pi "
                "или используйте mock-бэкенд."
            ) from exc

        # Настройка GPIO выполняется один раз при создании объекта.
        self._gpio = gpio
        self._gpio.setmode(self._gpio.BCM)
        self._gpio.setup(self.pin, self._gpio.OUT)
        self._pwm = self._gpio.PWM(self.pin, self.frequency_hz)

    def start(self, duty_cycle_percent: float) -> None:
        with self._lock:
            # RPi.GPIO ожидает float проценты (0..100).
            self._pwm.start(float(duty_cycle_percent))
            self._started = True

    def change_duty_cycle(self, duty_cycle_percent: float) -> None:
        with self._lock:
            # Некоторые реализации требуют start() перед первым ChangeDutyCycle().
            if not self._started:
                self._pwm.start(float(duty_cycle_percent))
                self._started = True
                return
            self._pwm.ChangeDutyCycle(float(duty_cycle_percent))

    def stop(self) -> None:
        with self._lock:
            if self._started:
                self._pwm.stop()
            self._started = False

    def close(self) -> None:
        with self._lock:
            try:
                # Закрытие всегда пытается остановить PWM, даже если уже остановлен.
                self.stop()
            finally:
                # cleanup освобождает пин, чтобы последующие запуски не “залипали”.
                self._gpio.cleanup(self.pin)

