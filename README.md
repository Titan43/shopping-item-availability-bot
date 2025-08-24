# shopping-item-availability-bot

A Telegram bot that checks whether a product page shows as **available**.

## Features
- Users send a URL, the bot scrapes it with Requests + BeautifulSoup.
- Heuristic detection using common availability keywords/buttons (multi‑language).
- Optional CSS selector override.
- Dockerfile provided;

## Quick Start

1. Create a bot with @BotFather and get the token.
2. Build and run with Docker:
   ```bash
   docker build -t shopping-availability-bot .
   docker run --rm -e TELEGRAM_BOT_TOKEN=123:ABC shopping-availability-bot
   ```

### Usage
- In Telegram, send any of:
  - A message containing a URL (the bot will parse it automatically).
  - `/check <url>` — check availability once and save for periodic monitoring.
  - `/check <url> | <css selector>` — check a specific element.
  - `/list` — show your watched URLs with last known status.
  - `/unwatch <url>` — stop watching a URL and remove it from your watchlist.
- Status returned: **AVAILABLE**, **OUT_OF_STOCK**, or **UNKNOWN** (if heuristics cannot determine availability).

Notes:
- Sending a URL via `/check` automatically saves it to your watchlist.
- `UNKNOWN` may appear if:
  - The page uses heavy JavaScript rendering (BeautifulSoup sees no content).
  - No known availability keywords or clickable buttons are detected.
- You can pass a CSS selector to target a specific element if needed.

### Environment Variables

The bot can be configured using the following environment variables:

- `TELEGRAM_BOT_TOKEN` (required) — your Telegram bot token from @BotFather.
- `REQUEST_TIMEOUT` (optional, default `15.0`) — timeout in seconds for HTTP requests when scraping pages.
- `CHECK_INTERVAL_MINUTES` (optional, default `180`) — interval in minutes for periodic availability checks of watched URLs.
- `SUBSCRIPTIONS_PATH` (optional, default `subscriptions.json`) — path to the JSON file where watchlist subscriptions are stored.
- `USER_AGENT` (optional) — custom User-Agent string for HTTP requests. Defaults to a modern Chrome Linux UA:
