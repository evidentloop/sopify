"""Plan intent detection for Sopify runtime.

Determines whether a user request explicitly asks for a new plan,
distinguishing genuine "create new plan" phrases from negated forms.
"""

from __future__ import annotations

import re
from typing import Sequence

_EXPLICIT_NEW_PLAN_PATTERNS = (
    re.compile(r"\bnew\s+plan\b", re.IGNORECASE),
    re.compile(r"\bcreate\s+(?:a\s+)?new\s+plan\b", re.IGNORECASE),
    re.compile(r"新建(?:一个)?\s*plan", re.IGNORECASE),
    re.compile(r"新\s*plan", re.IGNORECASE),
    re.compile(r"新的\s*plan", re.IGNORECASE),
    re.compile(r"另起(?:一个)?\s*plan", re.IGNORECASE),
    re.compile(r"新增(?:一个)?\s*plan", re.IGNORECASE),
)
_NEGATED_NEW_PLAN_PATTERNS = (
    re.compile(
        r"(?:不要|别|不用|无需|禁止)\s*(?:再|另外|额外|单独)?\s*(?:新建(?:一个)?(?:新的)?\s*plan|新\s*plan|新的\s*plan)",
        re.IGNORECASE,
    ),
    re.compile(r"(?:do\s+not|don't|dont|no\s+need\s+to)\s+(?:create\s+(?:a\s+)?new\s+plan|new\s+plan)", re.IGNORECASE),
)


def request_explicitly_wants_new_plan(request_text: str) -> bool:
    normalized = " ".join(request_text.split())
    matches = _collect_new_plan_intent_matches(normalized)
    effective_matches = _drop_positive_matches_covered_by_negated(matches)
    if not effective_matches:
        return False
    last_match = max(effective_matches, key=lambda item: (item[0], item[1]))
    return last_match[2] == "positive"


def _collect_new_plan_intent_matches(text: str) -> list[tuple[int, int, str]]:
    seen: set[tuple[int, int, str]] = set()
    ordered: list[tuple[int, int, str]] = []
    for polarity, patterns in (
        ("negated", _NEGATED_NEW_PLAN_PATTERNS),
        ("positive", _EXPLICIT_NEW_PLAN_PATTERNS),
    ):
        for pattern in patterns:
            for match in pattern.finditer(text):
                span = (match.start(), match.end(), polarity)
                if span in seen:
                    continue
                seen.add(span)
                ordered.append(span)
    return ordered


def _drop_positive_matches_covered_by_negated(
    matches: Sequence[tuple[int, int, str]],
) -> list[tuple[int, int, str]]:
    negated_spans = [(start, end) for start, end, polarity in matches if polarity == "negated"]
    effective: list[tuple[int, int, str]] = []
    for start, end, polarity in matches:
        if polarity == "positive" and any(neg_start <= start and end <= neg_end for neg_start, neg_end in negated_spans):
            continue
        effective.append((start, end, polarity))
    return effective
