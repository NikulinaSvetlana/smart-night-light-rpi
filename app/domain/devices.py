"""Реестр устройств и типы устройств (доменный слой).

Доменный слой — это “язык предметной области” без привязки к HTTP/FastAPI.
Он отвечает на вопросы:
- какие устройства есть в системе,
- как получить их текущее состояние,
- какие команды поддерживаются (включение/яркость),
- как корректно освободить ресурсы.

В MVP реестр in-memory и потокобезопасный, чтобы:
- можно было безопасно дергать API параллельно,
- не думать о внешних БД/очередях в ранней версии.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

from app.gpio.base import LedState
from app.gpio.led import LedController


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    """Публичные метаданные устройства."""

    device_id: str
    device_type: str


@dataclass(slots=True)
class LedDevice:
    """Обёртка LED-устройства."""

    device_id: str
    controller: LedController

    def info(self) -> DeviceInfo:
        """Вернуть метаданные устройства."""

        # В домене тип устройства задаём явно строкой.
        return DeviceInfo(device_id=self.device_id, device_type="led")

    def state(self) -> LedState:
        """Вернуть текущее состояние устройства."""

        return self.controller.state()

    def set_power(self, is_on: bool) -> LedState:
        """Включить или выключить питание."""

        return self.controller.set_power(is_on)

    def set_brightness(self, brightness: float) -> LedState:
        """Установить яркость (0..1)."""

        return self.controller.set_brightness(brightness)

    def close(self) -> None:
        """Освободить ресурсы."""

        self.controller.close()


class DeviceRegistry:
    """Потокобезопасный реестр устройств в памяти."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._led_devices: dict[str, LedDevice] = {}

    def register_led(self, device: LedDevice) -> None:
        """Зарегистрировать LED-устройство."""

        # Регистрируем по device_id — это ключ для API и сценариев.
        with self._lock:
            self._led_devices[device.device_id] = device

    def list_devices(self) -> list[DeviceInfo]:
        """Вернуть список всех зарегистрированных устройств."""

        with self._lock:
            return [d.info() for d in self._led_devices.values()]

    def get_led(self, device_id: str) -> LedDevice:
        """Получить устройство по идентификатору."""

        with self._lock:
            device = self._led_devices.get(device_id)
            if device is None:
                # В домене используем KeyError — транспортный слой решает,
                # как преобразовать это в HTTP-ошибку.
                raise KeyError(device_id)
            return device

    def close(self) -> None:
        """Закрыть все устройства."""

        with self._lock:
            devices = list(self._led_devices.values())
            self._led_devices.clear()

        # Закрываем устройства вне lock, чтобы не держать блокировку
        # на долгих операциях.
        for device in devices:
            device.close()
