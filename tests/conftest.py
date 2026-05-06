"""Pytest конфигурация для проекта.

Тесты запускаются из корня репозитория, но при некоторых способах запуска
(IDE, разные рабочие директории) Python может не видеть пакет `app`.

Чтобы тесты были стабильными и не зависели от текущей директории, мы
добавляем корень проекта в sys.path.

Это “прагматичное” решение для MVP: альтернативой было бы установка пакета
в окружение (pip install -e .) или настройка PYTHONPATH везде.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    # Ставим в начало, чтобы импортировался именно код из репозитория,
    # а не из site-packages.
    sys.path.insert(0, str(PROJECT_ROOT))
