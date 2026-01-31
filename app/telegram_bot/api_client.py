"""HTTP-клиент для API ночника, используемый Telegram-ботом.

Здесь нет логики Telegram — только тонкая обёртка над HTTP вызовами к API.
Это важно, потому что:
- код бота остаётся “чистым” и читабельным (команды -> вызов клиента -> ответ),
- HTTP-детали (URL, заголовки, verify TLS, таймауты) сосредоточены в одном месте,
- клиент легко мокать в тестах (или заменить другой реализацией при необходимости).

Клиент использует Bearer-токен (как и веб UI):
Authorization: Bearer <token>
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import httpx


@dataclass(frozen=True, slots=True)
class NightlightApiClient:
    """Клиент, который умеет делать базовые операции над ночником.

base_url:
- адрес API (например, https://localhost:8443)
api_token:
- общий токен доступа к API
device_id:
- идентификатор устройства (по умолчанию "nightlight")
tls_verify:
- проверять ли TLS-сертификат (в dev иногда отключают для self-signed)
"""

    base_url: str
    api_token: str
    device_id: str
    tls_verify: bool = True

    async def get_state(self) -> dict[str, Any]:
        """Получить текущее состояние устройства."""
        async with httpx.AsyncClient(
            base_url=self.base_url, timeout=10.0, verify=self.tls_verify
        ) as client:
            resp = await client.get(
                f"/api/v1/devices/{self.device_id}/state",
                # Токен передаётся на каждый запрос, чтобы клиент был stateless.
                headers={"Authorization": f"Bearer {self.api_token}"},
            )
            # Любая не-2xx ошибка превращается в исключение — это упрощает код бота.
            resp.raise_for_status()
            return cast(dict[str, Any], resp.json())

    async def set_power(self, is_on: bool) -> dict[str, Any]:
        """Включить/выключить устройство и вернуть новое состояние."""
        async with httpx.AsyncClient(
            base_url=self.base_url, timeout=10.0, verify=self.tls_verify
        ) as client:
            resp = await client.post(
                f"/api/v1/devices/{self.device_id}/power",
                headers={"Authorization": f"Bearer {self.api_token}"},
                json={"is_on": is_on},
            )
            resp.raise_for_status()
            return cast(dict[str, Any], resp.json())

    async def set_brightness(self, brightness: float) -> dict[str, Any]:
        """Установить яркость (0..1) и вернуть новое состояние."""
        async with httpx.AsyncClient(
            base_url=self.base_url, timeout=10.0, verify=self.tls_verify
        ) as client:
            resp = await client.post(
                f"/api/v1/devices/{self.device_id}/brightness",
                headers={"Authorization": f"Bearer {self.api_token}"},
                json={"brightness": brightness},
            )
            resp.raise_for_status()
            return cast(dict[str, Any], resp.json())
