"""Точка входа Telegram-бота.

Запускается отдельно от API-сервиса и управляет устройством через HTTP:
- читает настройки из окружения (Settings),
- создаёт Telegram Application,
- запускает polling (бот сам опрашивает Telegram API).

Почему polling, а не webhook:
- проще для MVP (не нужен публичный URL для самого бота),
- работает в локальной сети и в dev-окружениях,
- достаточно для “домашнего” сценария.
"""

from __future__ import annotations

from app.config import Settings
from app.logging_config import configure_logging

from .bot import create_bot


def main() -> None:
    """Запустить Telegram-бота в режиме polling."""
    settings = Settings()  # type: ignore[call-arg]
    # Используем те же настройки логирования, что и у API, чтобы логи были единообразны.
    configure_logging(settings.log_level)
    bot = create_bot(settings)
    # close_loop=False: оставляем управление event loop библиотеке,
    # чтобы избежать конфликтов.
    bot.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
