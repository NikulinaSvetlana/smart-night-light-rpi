"""Абстракции GPIO.

Проект поддерживает несколько окружений:
- Реальное железо Raspberry Pi через PWM в RPi.GPIO.
- Окружения разработки и CI через мок-бэкенд в памяти.

Здесь нет конкретных реализаций, только контракт (Protocol) и простые типы.
Это позволяет писать остальной код (контроллеры, домен, API) так, чтобы он:
- работал с настоящим GPIO на Raspberry Pi,
- работал в Docker/CI без GPIO, используя mock,
- был тестируемым и расширяемым.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class PwmOutput(Protocol):
    """Выходной пин с поддержкой PWM.

Это минимальный контракт, который должен уметь любой GPIO-бэкенд.
Методы соответствуют жизненному циклу PWM:
- start: первичный запуск,
- change_duty_cycle: обновление скважности,
- stop: остановка,
- close: освобождение ресурсов/cleanup.
"""

    def start(self, duty_cycle_percent: float) -> None:
        """Запустить PWM с заданной скважностью (0..100).

Обычно вызывается при первом включении или при первом ненулевом duty-cycle.
"""

    def change_duty_cycle(self, duty_cycle_percent: float) -> None:
        """Изменить скважность (0..100).

Бэкенд может сам решать, нужно ли делать start() перед первым изменением.
"""

    def stop(self) -> None:
        """Остановить PWM-выход.

После stop() ожидается, что устройство физически “погаснет”.
"""

    def close(self) -> None:
        """Освободить ресурсы GPIO.

Гарантирует, что бэкенд выполнит cleanup (например, gpio.cleanup()).
"""


@dataclass(frozen=True, slots=True)
class LedState:
    """Текущее состояние LED.

Состояние возвращается клиентам через API и используется в тестах.
brightness — всегда нормализована в диапазоне 0..1.
"""

    is_on: bool
    brightness: float
