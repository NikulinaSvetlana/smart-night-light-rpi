"""API сценариев (MVP).

Сценарий — это “рецепт” из действий, которые применяются к устройствам.
В текущем MVP:
- сценарии хранятся в памяти процесса (без БД),
- запуск только вручную через HTTP (без расписания),
- действия описываются простыми dict-объектами, чтобы легко расширять список.

Эндпоинты:
- GET /api/v1/scenarios: список сценариев,
- PUT /api/v1/scenarios/{id}: создать/обновить сценарий,
- POST /api/v1/scenarios/{id}/trigger: выполнить действия сценария.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.auth import AuthContext
from app.api.deps import get_auth, get_registry
from app.domain.devices import DeviceRegistry
from app.domain.scenarios import Scenario, ScenarioRegistry

router = APIRouter(prefix="/api/v1", tags=["scenarios"])


class ScenarioOut(BaseModel):
    """Схема ответа сценария."""
    scenario_id: str
    name: str
    actions: list[dict[str, Any]] = Field(default_factory=list)


class ScenarioUpsertIn(BaseModel):
    """Схема входных данных для создания/обновления сценария."""
    name: str = Field(min_length=1)
    actions: list[dict[str, Any]] = Field(default_factory=list)


def get_scenarios(request: Request) -> ScenarioRegistry:
    """Достать реестр сценариев из состояния приложения."""
    return cast(ScenarioRegistry, request.app.state.scenarios)


@router.get("/scenarios", response_model=list[ScenarioOut])
def list_scenarios(
    registry: ScenarioRegistry = Depends(get_scenarios),
    _auth: AuthContext = Depends(get_auth),
) -> list[ScenarioOut]:
    """Вернуть список сценариев."""
    return [
        ScenarioOut(scenario_id=s.scenario_id, name=s.name, actions=s.actions)
        for s in registry.list()
    ]


@router.put("/scenarios/{scenario_id}", response_model=ScenarioOut)
def upsert_scenario(
    scenario_id: str,
    payload: ScenarioUpsertIn,
    registry: ScenarioRegistry = Depends(get_scenarios),
    _auth: AuthContext = Depends(get_auth),
) -> ScenarioOut:
    """Создать или обновить сценарий."""
    scenario = Scenario(
        scenario_id=scenario_id.strip(),
        name=payload.name,
        actions=payload.actions,
    )
    registry.upsert(scenario)
    return ScenarioOut(
        scenario_id=scenario.scenario_id,
        name=scenario.name,
        actions=scenario.actions,
    )


@router.post("/scenarios/{scenario_id}/trigger")
def trigger_scenario(
    scenario_id: str,
    scenarios: ScenarioRegistry = Depends(get_scenarios),
    devices: DeviceRegistry = Depends(get_registry),
    _auth: AuthContext = Depends(get_auth),
) -> dict[str, Any]:
    """Запустить сценарий и вернуть список реально выполненных действий.

В MVP мы “молча пропускаем” некорректные действия:
- если нет device_id,
- если неизвестный type,
чтобы клиент мог постепенно усложнять сценарии, не ломая весь запуск.
"""
    try:
        scenario = scenarios.get(scenario_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        ) from exc

    executed: list[dict[str, Any]] = []
    for action in scenario.actions:
        # Действия — это словари, чтобы формат можно было менять без миграций.
        action_dict = action
        action_type = str(action_dict.get("type", "")).strip()
        device_id = str(action_dict.get("device_id", "")).strip()
        if not device_id:
            continue
        if action_type == "set_power":
            # set_power: включает/выключает устройство.
            is_on = bool(action_dict.get("is_on", False))
            state = devices.get_led(device_id).set_power(is_on)
            executed.append(
                {"type": action_type, "device_id": device_id, "state": asdict(state)}
            )
        elif action_type == "set_brightness":
            # set_brightness: задаёт яркость 0..1.
            brightness = float(action_dict.get("brightness", 0.0))
            state = devices.get_led(device_id).set_brightness(brightness)
            executed.append(
                {"type": action_type, "device_id": device_id, "state": asdict(state)}
            )

    return {"scenario_id": scenario.scenario_id, "executed": executed}
