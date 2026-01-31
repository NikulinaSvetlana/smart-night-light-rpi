"""Минимальный веб-интерфейс для управления ночником.

Это не “полноценный фронтенд”, а удобная страничка для ручной проверки:
- сохранить API токен в localStorage,
- включить/выключить устройство,
- поменять яркость,
- посмотреть текущий JSON-статус.

Весь UI лежит в app/web (HTML/CSS/JS) и раздаётся как статика.
Этот роут просто отдаёт index.html, а файлы по /static/ монтируются в factory.py.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["web"])


@router.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Отдать главную HTML-страницу веб-интерфейса."""
    root = Path(__file__).resolve().parents[1]
    web_dir = root / "web"
    return FileResponse(web_dir / "index.html")
