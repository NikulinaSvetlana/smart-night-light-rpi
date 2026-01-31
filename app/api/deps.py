"""Зависимости FastAPI.

Здесь описаны функции, которые FastAPI использует как dependency injection.
Идея проста:
- всё состояние приложения складываем в app.state при создании (см. factory.py),
- на каждом запросе зависимости вытаскивают нужный объект из Request,
- роуты объявляют нужные зависимости через Depends(...).

Плюсы такого подхода:
- нет глобальных переменных/синглтонов,
- тесты могут создавать приложение с любыми настройками,
- логика аутентификации вынесена в один слой.
"""

from __future__ import annotations

from typing import cast

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.auth import AuthContext, require_auth
from app.config import Settings
from app.domain.devices import DeviceRegistry

_bearer_scheme = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> Settings:
    """Получить настройки из состояния приложения."""

    # В factory.py это кладётся в app.state.settings.
    return cast(Settings, request.app.state.settings)


def get_registry(request: Request) -> DeviceRegistry:
    """Получить реестр устройств из состояния приложения."""

    # В factory.py это кладётся в app.state.registry.
    return cast(DeviceRegistry, request.app.state.registry)


def get_auth(
    settings: Settings = Depends(get_settings),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AuthContext:
    """Получить контекст аутентификации для запроса."""

    # Единственная точка входа в auth для роутов — require_auth.
    return require_auth(settings, credentials)
