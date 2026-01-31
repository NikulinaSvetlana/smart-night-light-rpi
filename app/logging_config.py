"""Конфигурация логирования.

Логирование в проекте настраивается централизованно через dictConfig, чтобы:
- получить единый формат сообщений во всех модулях,
- не зависеть от сторонних библиотек/обвязок,
- позволить тестам и CLI-скриптам включать логирование одинаково.

Мы сознательно используем “корневой” логгер:
- все модули пишут через logging.getLogger(<name>),
- уровень и обработчики задаются один раз,
- disable_existing_loggers=False оставляет логи зависимостей видимыми (если нужно).

Примечание: если захочется более продвинутой схемы (JSON-логи, file handler,
ротация, структурированные поля), это расширяется в одном месте.
"""

from __future__ import annotations

import logging
import logging.config


def configure_logging(level: str) -> None:
    """Настроить логирование приложения для вывода в консоль."""

    # dictConfig позволяет описать конфигурацию как обычный dict,
    # который легко сериализовать/шарить между окружениями.
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    # Формат выбран “человеческий”: время, уровень,
                    # имя логгера и сообщение.
                    "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
                }
            },
            "handlers": {
                "console": {
                    # StreamHandler пишет в stderr, что удобно для контейнеров/сервисов.
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            # Корневой логгер: единая точка, куда сходятся все логи.
            "root": {"handlers": ["console"], "level": level},
        }
    )
