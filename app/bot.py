from __future__ import annotations
import logging
import re
from datetime import timedelta
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from .config import TELEGRAM_BOT_TOKEN, CHECK_INTERVAL_MINUTES
from .scraper import check_availability
from . import storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logging.getLogger("httpx").setLevel(logging.WARNING)

log = logging.getLogger("bot")


def _parse_check_args(text: str) -> tuple[str, Optional[str]]:
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        raise ValueError(
            "Usage: /check <url> or /check <url> | <css selector>")
    payload = parts[1].strip()
    if " | " in payload:
        url, css = payload.split(" | ", 1)
        return url.strip(), css.strip()
    return payload, None


def _esc(s: str) -> str:
    return re.sub(r"([_*\[\]()~`>#+\-=|{}.!])", r"\\\1", s or "")


async def reply_availability(update: Update, result) -> None:
    title = f"<b>{result.title}</b>\n" if result.title else ""
    await update.message.reply_html(
        f"{title}<b>Status:</b> {result.status}\n<b>URL:</b> {result.url}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Send me a product URL and I'll check availability.\n"
        "Commands:\n"
        "• /check <url>\n"
        "• /check <url> | <css selector>\n"
        "• /list — show your watched URLs\n"
        "• /unwatch <url> — stop watching a URL"
    )


async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        url, css = _parse_check_args(update.message.text)
    except Exception as e:
        await update.message.reply_text(str(e))
        return

    await update.message.chat.send_action("typing")
    result = check_availability(url, css_selector=css)
    await reply_availability(update, result)

    # Save subscription (persisted file with guard)
    await storage.add(update.effective_user.id, url, result.status, css)
    await update.message.reply_text("Saved ✅ I’ll keep checking this link periodically.")


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    entries = await storage.list_user(update.effective_user.id)
    if not entries:
        await update.message.reply_text("You aren't watching any URLs yet.")
        return
    lines = [
        f"{i+1}. {e['url']} (last: {e.get('last_status','UNKNOWN')})"
        for i, e in enumerate(entries)
    ]
    await update.message.reply_text("Your watchlist:\n" + "\n".join(lines))


async def cmd_unwatch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /unwatch <url>")
        return
    url = context.args[0].strip()
    removed = await storage.remove(update.effective_user.id, url)
    if removed:
        await update.message.reply_text(f"Removed from watchlist: {url}")
    else:
        await update.message.reply_text("That URL wasn't in your watchlist.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Plain-text URL messages: check once (not auto-save)."""
    text = update.message.text or ""
    m = re.search(r"https?://\S+", text)
    if not m:
        await update.message.reply_text("Please send a product URL or use /check <url>")
        return
    url = m.group(0)
    await update.message.chat.send_action("typing")
    result = check_availability(url, css_selector=None)
    await reply_availability(update, result)
    await update.message.reply_text("Tip: use /check <url> to monitor it periodically.")


async def periodic_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run every CHECK_INTERVAL_MINUTES; notify when status changes to AVAILABLE."""
    log.info("Running periodic availability checks...")
    all_subs = await storage.get_all()
    for user_id_str, entries in all_subs.items():
        user_id = int(user_id_str)
        for e in entries:
            url = e["url"]
            css = e.get("css")
            prev = e.get("last_status", "UNKNOWN")
            result = check_availability(url, css_selector=css)
            await storage.update_status(user_id, url, result.status)

            if result.status == "AVAILABLE" and prev != "AVAILABLE":
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"✅ Item is now AVAILABLE:\n{url}"
                    )
                except Exception as ex:
                    log.error(
                        "Failed to send message to %s for %s: %s", user_id, url, ex)


def run() -> None:
    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("unwatch", cmd_unwatch))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message))

    app.job_queue.run_repeating(
        periodic_check,
        interval=timedelta(minutes=CHECK_INTERVAL_MINUTES),
        first=timedelta(seconds=60),
        name="periodic_check",
    )

    log.info("Bot starting...")
    app.run_polling(close_loop=False, timeout=2)
