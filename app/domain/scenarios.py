"""Сценарии автоматизации (MVP-заглушка).

В MVP сценарии хранятся в памяти и запускаются вручную.
Модуль оставляет возможность заменить хранилище на БД и добавить планировщики.

Словарь actions специально оставлен “нестрогим”:
- в MVP мы не вводим отдельные классы/enum для каждого действия,
- сценарии легко хранить и редактировать через JSON,
- API может добавлять новые действия без сложных миграций.

Ограничения MVP:
- нет валидации структуры actions на уровне домена,
- нет расписания/cron,
- нет персистентности (после перезапуска сценарии пропадут).
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any


@dataclass(frozen=True, slots=True)
class Scenario:
    """Описание сценария автоматизации.

scenario_id:
- стабилен и используется в URL,
- лучше делать коротким и человекочитаемым (например, "evening").
"""

    scenario_id: str
    name: str
    actions: list[dict[str, Any]]


class ScenarioRegistry:
    """Реестр сценариев в памяти."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._scenarios: dict[str, Scenario] = {}

    def list(self) -> list[Scenario]:
        """Вернуть список сценариев."""

        # Возвращаем копию списка, чтобы внешние вызовы не держали блокировку.
        with self._lock:
            return list(self._scenarios.values())

    def upsert(self, scenario: Scenario) -> None:
        """Создать или обновить сценарий."""

        # Upsert упрощает API: один endpoint и для создания, и для обновления.
        with self._lock:
            self._scenarios[scenario.scenario_id] = scenario

    def get(self, scenario_id: str) -> Scenario:
        """Получить сценарий."""

        with self._lock:
            scenario = self._scenarios.get(scenario_id)
            if scenario is None:
                # Домен возвращает KeyError, транспортный слой сам решит, что это 404.
                raise KeyError(scenario_id)
            return scenario

