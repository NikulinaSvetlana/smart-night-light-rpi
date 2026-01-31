"""Пакет приложения FastAPI.

Содержит:
- фабрику приложения (factory.py),
- зависимости (deps.py),
- схемы/контракты (schemas.py),
- роуты API (routes_*.py),
- entrypoint `app` для ASGI-сервера (app.py).

Идея: транспортный слой (HTTP) изолирован от домена и GPIO.
"""
