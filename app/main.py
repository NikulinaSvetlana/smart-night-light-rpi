"""Точка входа сервиса для локального запуска и Docker.

Этот модуль нужен, когда сервис запускают как “обычную программу”:

python -m app.main

В отличие от запуска через `uvicorn app.api.app:app`, здесь можно удобно:
- включить HTTPS (ssl_certfile / ssl_keyfile из Settings),
- передать host/port через переменные окружения,
- сохранить единый способ запуска в Docker/на железе.

Примечание:
- для разработки без TLS удобнее запускать uvicorn напрямую,
- для интеграций (Telegram-бот) чаще нужен HTTPS и понятный публичный URL.
"""

from __future__ import annotations

import os

import uvicorn

from app.api.factory import create_app
from app.config import Settings


def main() -> None:
    """Запустить HTTP(S) сервер Uvicorn с настройками из окружения."""
    settings = Settings()  # type: ignore[call-arg]
    # Эти переменные не входят в Settings, потому что относятся к “процессу сервера”,
    # а не к доменной конфигурации устройства.
    host = os.getenv("NIGHTLIGHT_HOST", "0.0.0.0")
    port = int(os.getenv("NIGHTLIGHT_PORT", "8443"))
    app = create_app(settings=settings)
    uvicorn.run(
        app,
        host=host,
        port=port,
        # Если ssl_* не задан — сервер поднимется по HTTP.
        ssl_certfile=settings.ssl_certfile,
        ssl_keyfile=settings.ssl_keyfile,
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()
