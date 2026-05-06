"""Интеграционные тесты HTTP API.

Эти тесты проверяют “сшивку” слоёв:
- FastAPI роуты,
- зависимости (settings/registry/auth),
- доменную логику LED-контроллера.

Важно: используем mock GPIO-бэкенд, поэтому тесты не требуют Raspberry Pi.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.factory import create_app
from app.config import Settings


def _client() -> TestClient:
    """Создать тестовый клиент с предсказуемыми настройками."""
    settings = Settings(
        api_token="test_token_1234567890",
        gpio_backend="mock",
        device_id="nightlight",
    )
    app = create_app(settings=settings)
    return TestClient(app)


def test_health_no_auth() -> None:
    """/health должен отвечать без токена, чтобы мониторинг был простым."""
    client = _client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_auth_required_for_device_state() -> None:
    """Доступ к управлению устройствами защищён Bearer-токеном."""
    client = _client()
    resp = client.get("/api/v1/devices/nightlight/state")
    assert resp.status_code == 401


def test_set_brightness_and_read_state() -> None:
    """POST яркости должен менять состояние и GET должен видеть новое значение."""
    client = _client()
    # В тестах храним токен рядом, чтобы не “магичить” строками по файлу.
    headers = {"Authorization": "Bearer test_token_1234567890"}

    resp = client.post(
        "/api/v1/devices/nightlight/brightness",
        json={"brightness": 0.25},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_on"] is True
    assert resp.json()["brightness"] == 0.25

    resp = client.get("/api/v1/devices/nightlight/state", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["brightness"] == 0.25


def test_status_includes_led_states() -> None:
    """Диагностический /status должен содержать состояния LED-устройств."""
    client = _client()
    headers = {"Authorization": "Bearer test_token_1234567890"}
    resp = client.get("/status", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "led_states" in data
    assert "nightlight" in data["led_states"]
