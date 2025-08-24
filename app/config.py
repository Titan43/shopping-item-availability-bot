import os
from pathlib import Path


def safe_float(env_value, default):
    try:
        return float(env_value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

REQUEST_TIMEOUT = safe_float(os.environ.get("REQUEST_TIMEOUT"), 15.0)
CHECK_INTERVAL_MINUTES = _safe_int(
    os.environ.get("CHECK_INTERVAL_MINUTES"), 180)

SUBSCRIPTIONS_PATH = Path(os.environ.get(
    "SUBSCRIPTIONS_PATH", "/app/data/subscriptions.json"))

USER_AGENT = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
)
