from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional, Tuple

import cloudscraper
from bs4 import BeautifulSoup

from .config import REQUEST_TIMEOUT, USER_AGENT

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Referer": "",
}

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


def fetch_html(url: str) -> Tuple[str, str]:
    scraper = cloudscraper.create_scraper()
    resp = scraper.get(url, headers=HEADERS,
                       timeout=REQUEST_TIMEOUT, allow_redirects=True)
    resp.raise_for_status()
    return resp.url, resp.text


def check_keywords(text: str) -> Optional[Tuple[str, str]]:
    lower = text.lower()
    for kw in AVAILABILITY_KEYWORDS["unavailable"]:
        if kw.lower() in lower:
            return "OUT_OF_STOCK", f"Matched keyword: {kw}"
    for kw in AVAILABILITY_KEYWORDS["available"]:
        if kw.lower() in lower:
            return "AVAILABLE", f"Matched keyword: {kw}"
    return None


def check_availability(url: str, css_selector: Optional[str] = None) -> CheckResult:
    try:
        final_url, html = fetch_html(url)
    except Exception as e:
        return CheckResult(status="UNKNOWN", reason=f"Request failed: {e}", url=url)

    soup = BeautifulSoup(html, "html5lib")
    page_text = soup.get_text(separator=" ", strip=True)

    if css_selector:
        try:
            nodes = soup.select(css_selector)
            if not nodes:
                return CheckResult(
                    status="UNKNOWN",
                    reason=f"CSS selector '{css_selector}' matched nothing.",
                    title=soup.title.string.strip() if soup.title else None,
                    url=final_url,
                )
            zone_text = " ".join(n.get_text(
                separator=" ", strip=True) for n in nodes)
            kw = check_keywords(zone_text)
            if kw:
                status, evidence = kw
                return CheckResult(
                    status=status,
                    reason=f"{evidence} (inside selector: {css_selector})",
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
