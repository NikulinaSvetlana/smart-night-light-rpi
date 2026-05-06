"""Unit-тесты утилит Telegram-бота.

В MVP мы тестируем минимум: парсинг аргумента яркости, потому что это
частый источник ошибок пользовательского ввода.
"""

from __future__ import annotations

from app.telegram_bot.bot import parse_brightness_arg


def test_parse_brightness_arg_clamps() -> None:
    """Значение яркости должно ограничиваться диапазоном 0..100%."""
    assert parse_brightness_arg("0") == 0.0
    assert parse_brightness_arg("100") == 1.0
    assert parse_brightness_arg("999") == 1.0
    assert parse_brightness_arg("-10") == 0.0
