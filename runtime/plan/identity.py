"""Plan identity helpers shared by scaffold creation and plan lookup."""

from __future__ import annotations

from hashlib import sha1
import re


def derive_topic_key(request_text: str) -> str:
    cleaned = " ".join(request_text.split())
    if not cleaned:
        return "task"
    normalized = _slugify(cleaned)[:48].rstrip("-")
    if normalized:
        return normalized
    return f"task-{sha1(cleaned.encode('utf-8')).hexdigest()[:6]}"


def _slugify(value: str) -> str:
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return ascii_slug or "task"
