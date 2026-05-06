"""Интеграционный тест сценариев.

Цель — проверить “сквозной” путь:
- создать сценарий через HTTP,
- запустить его,
- убедиться, что API отчитался о выполнении действий.

Внутреннее применение действий (включение/яркость) выполняется через доменный
реестр устройств, но мы проверяем результат на уровне API-ответа.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.factory import create_app
from app.config import Settings


def test_scenario_trigger_executes_actions() -> None:
    """Сценарий должен сохраняться и запускаться в пределах процесса."""
    settings = Settings(api_token="test_token_1234567890", gpio_backend="mock")
    app = create_app(settings=settings)
    client = TestClient(app)
    headers = {"Authorization": "Bearer test_token_1234567890"}

    # Создаём сценарий “evening” с двумя действиями.
    resp = client.put(
        "/api/v1/scenarios/evening",
        json={
            "name": "Evening",
            "actions": [
                {"type": "set_power", "device_id": "nightlight", "is_on": True},
                {
                    "type": "set_brightness",
                    "device_id": "nightlight",
                    "brightness": 0.4,
                },
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 200

    # Запускаем сценарий и проверяем отчёт о выполненных действиях.
    resp = client.post("/api/v1/scenarios/evening/trigger", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario_id"] == "evening"
    assert len(data["executed"]) >= 1
