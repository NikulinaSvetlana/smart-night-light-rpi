"""Моковый GPIO-бэкенд для разработки и тестирования.

Это “виртуальный PWM”, который:
- не управляет настоящими пинами,
- просто сохраняет состояние в памяти (started + duty_cycle_percent),
- позволяет тестировать поведение контроллера и API без Raspberry Pi.

Зачем lock:
- тесты/сервер могут вызывать методы параллельно,
- мы хотим, чтобы состояние менялось атомарно.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from .base import PwmOutput


@dataclass(slots=True)
class MockPwmOutput(PwmOutput):
    """Реализация PWM-выхода в памяти.

Достаточно простая модель:
- start() помечает started=True и сохраняет текущую скважность,
- change_duty_cycle() также “включает” PWM при первом вызове,
- stop() сбрасывает в 0.
"""

    frequency_hz: int
    duty_cycle_percent: float = 0.0
    started: bool = False
    _lock: Lock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # Lock создаём в __post_init__, чтобы не попадал в __init__-сигнатуру dataclass.
        self._lock = Lock()

    def start(self, duty_cycle_percent: float) -> None:
        with self._lock:
            self.started = True
            self.duty_cycle_percent = float(duty_cycle_percent)

    def change_duty_cycle(self, duty_cycle_percent: float) -> None:
        with self._lock:
            # На реальных PWM часто нельзя “менять” до start(), поэтому в мок-бэкенде
            # делаем поведение более удобным: change_duty_cycle автоматически запускает.
            if not self.started:
                self.started = True
            self.duty_cycle_percent = float(duty_cycle_percent)

    def stop(self) -> None:
        with self._lock:
            self.started = False
            self.duty_cycle_percent = 0.0

    def close(self) -> None:
        # У мок-бэкенда нет реальных ресурсов.
        return

