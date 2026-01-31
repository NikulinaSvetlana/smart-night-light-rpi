"""Драйвер LED, использующий PWM-выход.

Здесь находится простая бизнес-логика управления яркостью:
- яркость хранится как float 0..1,
- физическая “скважность” PWM вычисляется как brightness * 100,
- выключение приводит к остановке PWM и сбросу яркости в 0.

Почему отдельный контроллер:
- GPIO-бэкенды разные (mock/rpi), но поведение LED должно быть одинаковым,
- контроллер легко тестировать без настоящего железа,
- доменный слой работает с контроллером как с зависимостью.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from .base import LedState, PwmOutput


def _clamp(value: float, low: float, high: float) -> float:
    """Ограничить значение диапазоном [low, high]."""
    if value < low:
        return low
    if value > high:
        return high
    return value


@dataclass(slots=True)
class LedController:
    """Контроллер LED с поддержкой включения и яркости."""

    pwm: PwmOutput
    _lock: Lock = field(init=False, repr=False)
    _is_on: bool = field(init=False, default=False)
    _brightness: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        # Lock нужен, потому что API может дергаться параллельно.
        self._lock = Lock()

    def state(self) -> LedState:
        """Вернуть текущее состояние."""

        with self._lock:
            return LedState(is_on=self._is_on, brightness=self._brightness)

    def set_power(self, is_on: bool) -> LedState:
        """Включить или выключить LED."""

        with self._lock:
            if is_on:
                # При первом включении выставляем яркость в максимум,
                # чтобы “включить” выглядело ожидаемо.
                if self._brightness <= 0.0:
                    self._brightness = 1.0
                self._apply()
                self._is_on = True
            else:
                # Выключение: останавливаем PWM и сбрасываем значение яркости.
                self.pwm.stop()
                self._is_on = False
                self._brightness = 0.0
            return LedState(is_on=self._is_on, brightness=self._brightness)

    def set_brightness(self, brightness: float) -> LedState:
        """Установить яркость в диапазоне 0..1."""

        with self._lock:
            # Приводим к float и “срезаем” диапазон, чтобы избежать
            # некорректных значений.
            self._brightness = _clamp(float(brightness), 0.0, 1.0)
            if self._brightness == 0.0:
                # Нулевая яркость трактуется как выключение.
                self.pwm.stop()
                self._is_on = False
                return LedState(is_on=False, brightness=0.0)

            # Ненулевая яркость => устройство включено.
            self._is_on = True
            self._apply()
            return LedState(is_on=True, brightness=self._brightness)

    def close(self) -> None:
        """Освободить ресурсы."""

        with self._lock:
            try:
                self.pwm.stop()
            finally:
                self.pwm.close()

    def _apply(self) -> None:
        # Переводим нормализованную яркость в PWM-скважность.
        duty = self._brightness * 100.0
        self.pwm.change_duty_cycle(duty)
