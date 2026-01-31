"""Реализация Telegram-бота.

Этот бот — альтернативный “клиент” для управления ночником поверх HTTP API.
Архитектура намеренно простая:
- BotContext хранит всё “состояние” (HTTP-клиент + список разрешённых чатов),
- каждая команда Telegram вызывает соответствующий метод API,
- ответы формируются как обычный текст (без сложных клавиатур).

Зачем бот ходит в API, а не напрямую в GPIO:
- API остаётся единственной точкой управления устройством,
- одинаковые правила аутентификации/валидации для всех клиентов,
- проще разносить на разные процессы/контейнеры при росте проекта.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from app.config import Settings

from .api_client import NightlightApiClient


@dataclass(frozen=True, slots=True)
class BotContext:
    """Контекст бота, общий для всех обработчиков."""
    api: NightlightApiClient
    allowed_chat_ids: set[int]


def parse_brightness_arg(value: str) -> float:
    """Преобразовать яркость из "0..100" в значение 0..1."""

    text = value.strip()
    # Пользователь вводит проценты, а API ожидает 0..1.
    percent = int(text)
    if percent < 0:
        percent = 0
    if percent > 100:
        percent = 100
    return percent / 100.0


def create_bot(settings: Settings) -> Application[Any, Any, Any, Any, Any, Any]:
    """Создать приложение Telegram-бота."""

    if not settings.telegram_bot_token:
        # Токен для Telegram должен быть задан отдельно от токена API.
        raise RuntimeError("NIGHTLIGHT_TELEGRAM_BOT_TOKEN обязателен для запуска бота")

    # HTTP-клиент, который будет дергать FastAPI.
    api = NightlightApiClient(
        base_url=settings.telegram_api_url,
        api_token=settings.api_token,
        device_id=settings.device_id,
        tls_verify=settings.telegram_tls_verify,
    )
    # Ограничиваем доступ по chat_id, чтобы бот не управлялся “всем интернетом”.
    ctx = BotContext(api=api, allowed_chat_ids=settings.allowed_chat_ids())

    application = ApplicationBuilder().token(settings.telegram_bot_token).build()
    # BotData — стандартное место, где python-telegram-bot хранит произвольные данные.
    application.bot_data["ctx"] = ctx

    # Регистрируем команды. Каждая команда — отдельный handler-функция ниже.
    application.add_handler(CommandHandler("start", _start))
    application.add_handler(CommandHandler("status", _status))
    application.add_handler(CommandHandler("on", _on))
    application.add_handler(CommandHandler("off", _off))
    application.add_handler(CommandHandler("brightness", _brightness))
    return application


def _ctx(context: ContextTypes.DEFAULT_TYPE) -> BotContext:
    """Достать BotContext из application.bot_data."""
    return cast(BotContext, context.application.bot_data["ctx"])


def _is_allowed(update: Update, ctx: BotContext) -> bool:
    """Проверить, что чат имеет доступ к управлению ботом."""
    chat = update.effective_chat
    if chat is None:
        return False
    if not ctx.allowed_chat_ids:
        # Пустой allowlist означает “разрешено всем”
        # (удобно для локальных экспериментов).
        return True
    return chat.id in ctx.allowed_chat_ids


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start: показывает подсказку по командам."""
    ctx = _ctx(context)
    message = update.effective_message
    if message is None:
        return
    if not _is_allowed(update, ctx):
        await message.reply_text("Доступ запрещён.")
        return
    await message.reply_text("Команды: /status, /on, /off, /brightness 0-100")


async def _status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /status: читает состояние из API и показывает его пользователю."""
    ctx = _ctx(context)
    message = update.effective_message
    if message is None:
        return
    if not _is_allowed(update, ctx):
        await message.reply_text("Доступ запрещён.")
        return
    # API возвращает JSON с is_on/brightness.
    state = await ctx.api.get_state()
    brightness = int(round(float(state.get("brightness", 0.0)) * 100))
    is_on = bool(state.get("is_on", False))
    await message.reply_text(
        f"Состояние: {'ON' if is_on else 'OFF'}, яркость {brightness}%"
    )


async def _on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /on: включает устройство."""
    ctx = _ctx(context)
    message = update.effective_message
    if message is None:
        return
    if not _is_allowed(update, ctx):
        await message.reply_text("Доступ запрещён.")
        return
    state = await ctx.api.set_power(True)
    brightness = int(round(float(state.get("brightness", 0.0)) * 100))
    await message.reply_text(f"Включено, яркость {brightness}%")


async def _off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /off: выключает устройство."""
    ctx = _ctx(context)
    message = update.effective_message
    if message is None:
        return
    if not _is_allowed(update, ctx):
        await message.reply_text("Доступ запрещён.")
        return
    await ctx.api.set_power(False)
    await message.reply_text("Выключено")


async def _brightness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /brightness 0-100: задаёт яркость в процентах."""
    ctx = _ctx(context)
    message = update.effective_message
    if message is None:
        return
    if not _is_allowed(update, ctx):
        await message.reply_text("Доступ запрещён.")
        return
    if not context.args:
        await message.reply_text("Использование: /brightness 0-100")
        return
    try:
        brightness01 = parse_brightness_arg(context.args[0])
    except ValueError:
        # Пользователь мог прислать не число.
        await message.reply_text("Нужно число 0-100")
        return
    state = await ctx.api.set_brightness(brightness01)
    brightness = int(round(float(state.get("brightness", 0.0)) * 100))
    await message.reply_text(f"Установлено {brightness}%")
