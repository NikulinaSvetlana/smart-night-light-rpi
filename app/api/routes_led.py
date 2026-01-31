"""API для управления LED-устройствами.

Эндпоинты этого модуля — это “проводка” между HTTP и доменной моделью:
- аутентификация проверяется зависимостью get_auth,
- доступ к устройствам идёт через доменный реестр DeviceRegistry,
- вход/выход сериализуются Pydantic-схемами.

Важно:
- команды `power` и `brightness` возвращают новое состояние устройства, чтобы
  UI/клиенту не нужно было делать дополнительный GET,
- device_id — строковый идентификатор устройства (по умолчанию "nightlight").
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import AuthContext
from app.api.deps import get_auth, get_registry
from app.api.schemas import DeviceInfoOut, LedStateOut, SetBrightnessIn, SetPowerIn
from app.domain.devices import DeviceRegistry

router = APIRouter(prefix="/api/v1", tags=["devices"])


@router.get("/devices", response_model=list[DeviceInfoOut])
def list_devices(
    registry: DeviceRegistry = Depends(get_registry),
    _auth: AuthContext = Depends(get_auth),
) -> list[DeviceInfoOut]:
    """Вернуть список зарегистрированных устройств."""
    devices = registry.list_devices()
    return [
        DeviceInfoOut(device_id=d.device_id, device_type=d.device_type) for d in devices
    ]


@router.get("/devices/{device_id}/state", response_model=LedStateOut)
def get_led_state(
    device_id: str,
    registry: DeviceRegistry = Depends(get_registry),
    _auth: AuthContext = Depends(get_auth),
) -> LedStateOut:
    """Вернуть текущее состояние LED-устройства."""
    try:
        device = registry.get_led(device_id)
    except KeyError as exc:
        # Реестр кидает KeyError, а API переводит это в 404.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        ) from exc

    state = device.state()
    return LedStateOut(is_on=state.is_on, brightness=state.brightness)


@router.post("/devices/{device_id}/power", response_model=LedStateOut)
def set_led_power(
    device_id: str,
    payload: SetPowerIn,
    registry: DeviceRegistry = Depends(get_registry),
    _auth: AuthContext = Depends(get_auth),
) -> LedStateOut:
    """Установить питание LED-устройства (вкл/выкл) и вернуть новое состояние."""
    try:
        device = registry.get_led(device_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        ) from exc

    state = device.set_power(payload.is_on)
    return LedStateOut(is_on=state.is_on, brightness=state.brightness)


@router.post("/devices/{device_id}/brightness", response_model=LedStateOut)
def set_led_brightness(
    device_id: str,
    payload: SetBrightnessIn,
    registry: DeviceRegistry = Depends(get_registry),
    _auth: AuthContext = Depends(get_auth),
) -> LedStateOut:
    """Установить яркость LED-устройства и вернуть новое состояние."""
    try:
        device = registry.get_led(device_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        ) from exc

    state = device.set_brightness(payload.brightness)
    return LedStateOut(is_on=state.is_on, brightness=state.brightness)

