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
   docker build -t tg-availability-bot .
   docker run --rm -e TELEGRAM_BOT_TOKEN=123:ABC tg-availability-bot
   ```

### Usage
- In Telegram, send any of:
  - A message that contains a URL (the bot will try to parse it automatically).
  - `/check <url>`
  - `/check <url> | <css selector>` to target a specific element.
- The bot returns one of: **AVAILABLE**, **OUT_OF_STOCK**, or **UNKNOWN**, with evidence.

### Environment

- `TELEGRAM_BOT_TOKEN` (required)
- `REQUEST_TIMEOUT` (optional, seconds, default `15`)

## Limitations
- Some sites render content with heavy JavaScript; BeautifulSoup (no browser) may miss those.
- Rate limits and bot detection/captchas on some ecommerce sites can block scraping.
- Heuristics are best‑effort and may need adjustment per site; you can pass a CSS selector.