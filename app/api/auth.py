"""Аутентификация API (Bearer-токен).

Модель безопасности в проекте максимально простая: один общий токен
(shared secret), который клиенты передают в заголовке:

Authorization: Bearer <token>

Зачем так:
- для MVP этого достаточно (простота важнее сложной системы пользователей),
- легко подключить веб-страницу и Telegram-бота,
- легко оборачивается в HTTPS (см. app/main.py и переменные SSL_*).

Тонкости:
- сравнение токенов делаем через secrets.compare_digest, чтобы избежать
  тайминговых атак на сравнение строк,
- схема HTTPBearer объявлена с auto_error=False, чтобы самим контролировать
  формат ответа и не получать “магические” ошибки от middleware.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class AuthContext:
    """Информация об аутентифицированном вызывающем.

Пока здесь только subject, чтобы:
- логировать “кто” сделал запрос,
- в будущем расширить контекст (например, разные роли/клиенты).
"""

    subject: str


def require_auth(
    settings: Settings,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AuthContext:
    """Проверить, что Bearer-токен валиден, и вернуть контекст аутентификации."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        # Нет заголовка Authorization или неправильная схема — считаем неавторизованным.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    if not secrets.compare_digest(credentials.credentials, settings.api_token):
        # Токен передан, но не совпал с ожидаемым — тоже 401.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    return AuthContext(subject="api_token")
