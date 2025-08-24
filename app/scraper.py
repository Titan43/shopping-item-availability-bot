from __future__ import annotations
from dataclasses import dataclass
import re
import time
from typing import Optional, Tuple

import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

from .config import REQUEST_TIMEOUT, USER_AGENT

AVAILABILITY_KEYWORDS = {
    "available": [
        "available", "in stock", "add to cart", "buy now",
        "доступно", "в наявності", "в наличии", "доступен",
        "dodaj do koszyka", "kup teraz"
    ],
    "unavailable": [
        "out of stock", "not available", "sold out", "unavailable",
        "немає в наявності", "нет в наличии", "brak w magazynie",
        "niedostępny", "preorder"
    ]
}


@dataclass
class CheckResult:
    status: str  # AVAILABLE | OUT_OF_STOCK | UNKNOWN
    reason: str
    title: Optional[str] = None
    url: Optional[str] = None


def _make_driver() -> uc.Chrome:
    """Create undetected Chrome driver for Docker."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    chrome_options.add_argument(
        "--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = uc.Chrome(options=chrome_options)
    return driver


def fetch_html(url: str) -> Tuple[str, str]:
    driver = _make_driver()
    try:
        driver.set_page_load_timeout(REQUEST_TIMEOUT)
        driver.get(url)

        # Give JS time to render (adjust if needed)
        time.sleep(3)

        final_url = driver.current_url
        html = driver.page_source
        return final_url, html
    finally:
        driver.quit()


def normalize_text(t: str) -> str:
    return re.sub(r'[\"\']', '', t).strip().lower()


def check_keywords(text: str) -> Optional[Tuple[str, str]]:
    norm = normalize_text(text)
    for kw in AVAILABILITY_KEYWORDS["unavailable"]:
        if kw.lower() in norm:
            return "OUT_OF_STOCK", f"Matched keyword: {kw}"
    for kw in AVAILABILITY_KEYWORDS["available"]:
        if kw.lower() in norm:
            return "AVAILABLE", f"Matched keyword: {kw}"
    return None


def check_availability(url: str, css_selector: Optional[str] = None) -> CheckResult:
    try:
        final_url, html = fetch_html(url)
    except Exception as e:
        return CheckResult(status="UNKNOWN", reason=f"Request failed: {e}", url=url)

    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(separator=" ", strip=True)

    if css_selector:
        try:
            nodes = soup.select(css_selector)
            if not nodes:
                return CheckResult(
                    status="OUT_OF_STOCK",
                    reason=f"CSS selector '{css_selector}' matched nothing.",
                    title=soup.title.string.strip() if soup.title else None,
                    url=final_url,
                )
            return CheckResult(
                status="AVAILABLE",
                reason=f"Selector '{css_selector}' matched {len(nodes)} node(s).",
                title=soup.title.string.strip() if soup.title else None,
                url=final_url,
            )
        except Exception as e:
            return CheckResult(
                status="UNKNOWN",
                reason=f"CSS selector parse error: {e}",
                title=soup.title.string.strip() if soup.title else None,
                url=final_url,
            )

    kw = check_keywords(page_text)
    if kw:
        status, evidence = kw
        return CheckResult(
            status=status,
            reason=evidence,
            title=soup.title.string.strip() if soup.title else None,
            url=final_url,
        )

    # Heuristic: check for buttons
    button_texts = [
        "add to cart", "buy now", "в кошик", "у кошик", "купити", "в корзину",
        "додати до кошика", "додати в кошик", "dodaj do koszyka", "kup teraz"
    ]
    for btn in soup.find_all(["button", "a", "input"]):
        txt = btn.get_text(separator=" ", strip=True) if btn.name != "input" else (
            btn.get("value") or "")
        t = txt.lower()
        if any(b in t for b in button_texts):
            disabled = btn.get("disabled") is not None or "disabled" in (
                btn.get("class") or [])
            aria = btn.get("aria-disabled")
            if not disabled and str(aria).lower() not in {"true", "1"}:
                return CheckResult(
                    status="AVAILABLE",
                    reason=f"Clickable purchase control detected: {txt!r}",
                    title=soup.title.string.strip() if soup.title else None,
                    url=final_url,
                )

    sample = (page_text[:300] + "...") if len(page_text) > 300 else page_text
    return CheckResult(
        status="UNKNOWN",
        reason=f"No conclusive signals. Sample page text: {sample!r}",
        title=soup.title.string.strip() if soup.title else None,
        url=final_url,
    )
