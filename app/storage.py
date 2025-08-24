from __future__ import annotations
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional

from .config import SUBSCRIPTIONS_PATH

_SUBS_PATH = Path(SUBSCRIPTIONS_PATH)
_lock = asyncio.Lock()


async def _read() -> Dict[str, List[dict]]:
    async with _lock:
        if not _SUBS_PATH.exists():
            return {}
        try:
            data = json.loads(_SUBS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
            return {}
        except json.JSONDecodeError:
            # Corrupted file fallback
            return {}


async def _write(data: Dict[str, List[dict]]) -> None:
    async with _lock:
        tmp = _SUBS_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(
            data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(_SUBS_PATH)


async def get_all() -> Dict[str, List[dict]]:
    return await _read()


async def list_user(user_id: int) -> List[dict]:
    data = await _read()
    return data.get(str(user_id), [])


async def add(user_id: int, url: str, result: Optional[str] = "UNKNOWN", css: Optional[str] = None) -> None:
    data = await _read()
    key = str(user_id)
    entries = data.get(key, [])
    # Prevent duplicates (by URL+CSS)
    exists = any(e["url"] == url and (e.get("css") or None)
                 == (css or None) for e in entries)
    if not exists:
        entries.append({"url": url, "css": css, "last_status": result})
        data[key] = entries
        await _write(data)


async def remove(user_id: int, url: str) -> bool:
    data = await _read()
    key = str(user_id)
    entries = data.get(key, [])
    new_entries = [e for e in entries if e["url"] != url]
    changed = len(new_entries) != len(entries)
    if changed:
        if new_entries:
            data[key] = new_entries
        else:
            data.pop(key, None)
        await _write(data)
    return changed


async def update_status(user_id: int, url: str, new_status: str) -> None:
    data = await _read()
    key = str(user_id)
    entries = data.get(key, [])
    for e in entries:
        if e["url"] == url:
            e["last_status"] = new_status
            break
    data[key] = entries
    await _write(data)
