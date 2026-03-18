"""Decision-style facade contracts derived from structured compare results."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from .decision_templates import StrategyPickTemplate, build_strategy_pick_template
from .models import DecisionCheckpoint, DecisionOption, DecisionRecommendation

COMPARE_DECISION_CONTRACT_VERSION = "1"
COMPARE_DECISION_TYPE = "compare_result_choice"
_MAX_COMPARE_SHORTLIST = 3


def build_compare_decision_contract(
    *,
    question: str,
    skill_result: Mapping[str, Any],
    language: str,
) -> Mapping[str, Any] | None:
    """Build a host-consumable decision facade from compare runtime results.

    This keeps `~compare` on its existing route while letting hosts reuse the
    same `DecisionCheckpoint / DecisionSubmission` interaction model when they
    want to present a shortlist of compare outputs.
    """
    results = tuple(
        item
        for item in (skill_result.get("results") or ())
        if isinstance(item, Mapping)
        and str(item.get("status") or "").strip().lower() in {"ok", "success"}
        and str(item.get("answer") or "").strip()
    )
    if len(results) < 2:
        return None

    shortlisted = results[:_MAX_COMPARE_SHORTLIST]
    options = tuple(
        _result_to_option(result, index=index, language=language)
        for index, result in enumerate(shortlisted, start=1)
    )
    recommended_index, recommendation_reason = _recommend_shortlist(shortlisted, language=language)
    summary = _summary_for_language(language, result_count=len(results), shortlisted_count=len(shortlisted))
    rendered = build_strategy_pick_template(
        checkpoint_id=f"compare_decision_{_stable_slug(question)}",
        question=_question_for_language(language, question),
        summary=summary,
        options=options,
        language=language,
        recommended_option_id=options[recommended_index].option_id,
        default_option_id=options[recommended_index].option_id,
        allow_custom_option=False,
    )
    checkpoint = _with_recommendation_reason(
        rendered,
        recommendation_reason=recommendation_reason,
    )
    return {
        "contract_version": COMPARE_DECISION_CONTRACT_VERSION,
        "decision_type": COMPARE_DECISION_TYPE,
        "question": checkpoint.title,
        "summary": summary,
        "recommended_option_id": rendered.recommended_option_id,
        "default_option_id": rendered.default_option_id,
        "recommendation_reason": recommendation_reason,
        "result_count": len(results),
        "shortlisted_result_count": len(shortlisted),
        "checkpoint": checkpoint.to_dict(),
        "decision_submission_state": {
            "status": "empty",
            "source": None,
            "resume_action": None,
            "submitted_at": None,
            "has_answers": False,
            "answer_keys": [],
        },
    }


def _result_to_option(result: Mapping[str, Any], *, index: int, language: str) -> DecisionOption:
    candidate_id = str(result.get("candidate_id") or f"candidate_{index}")
    answer = str(result.get("answer") or "")
    latency_ms = int(result.get("latency_ms") or 0)
    summary = _answer_excerpt(answer)
    return DecisionOption(
        option_id=candidate_id,
        title=candidate_id,
        summary=summary,
        tradeoffs=(_latency_text(language, latency_ms),),
        impacts=(_impact_text(language),),
        recommended=False,
    )


def _recommend_shortlist(results: tuple[Mapping[str, Any], ...], *, language: str) -> tuple[int, str]:
    for index, result in enumerate(results):
        candidate_id = str(result.get("candidate_id") or "")
        normalized = candidate_id.casefold()
        if "default" in normalized or "session" in normalized:
            return index, _text(language, "recommend_default_baseline")
    return 0, _text(language, "recommend_first_success")


def _with_recommendation_reason(
    rendered: StrategyPickTemplate,
    *,
    recommendation_reason: str,
) -> DecisionCheckpoint:
    recommendation = rendered.checkpoint.recommendation
    if recommendation is None:
        return rendered.checkpoint
    return replace(
        rendered.checkpoint,
        recommendation=DecisionRecommendation(
            field_id=recommendation.field_id,
            option_id=recommendation.option_id,
            summary=recommendation.summary,
            reason=recommendation_reason,
        ),
    )


def _question_for_language(language: str, question: str) -> str:
    if language == "en-US":
        return f"Which compare result should guide the next step for: {question.strip() or 'this request'}?"
    return f"多模型对比已返回多个候选，接下来应以哪个结果为主推进：{question.strip() or '当前请求'}？"


def _summary_for_language(language: str, *, result_count: int, shortlisted_count: int) -> str:
    if language == "en-US":
        if result_count > shortlisted_count:
            return f"Shortlisted {shortlisted_count} compare results from {result_count} successful outputs. Confirm which one should guide the next step."
        return f"{result_count} successful compare results are available. Confirm which one should guide the next step."
    if result_count > shortlisted_count:
        return f"已从 {result_count} 个成功结果中收敛出 {shortlisted_count} 个候选，请确认后续重点采用哪一个。"
    return f"当前已有 {result_count} 个成功结果，请确认后续重点采用哪一个。"


def _latency_text(language: str, latency_ms: int) -> str:
    if language == "en-US":
        return f"Observed latency: {latency_ms} ms"
    return f"观测延迟：{latency_ms} ms"


def _impact_text(language: str) -> str:
    if language == "en-US":
        return "The host may reuse the same decision bridge UI instead of inventing a compare-specific picker."
    return "宿主可直接复用同一套 decision bridge UI，而不必再额外造 compare 专用选择器。"


def _answer_excerpt(answer: str, *, max_length: int = 180) -> str:
    normalized = " ".join(segment.strip() for segment in answer.splitlines() if segment.strip())
    if not normalized:
        return ""
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 1].rstrip() + "…"


def _stable_slug(text: str) -> str:
    normalized = "".join(char if char.isalnum() else "_" for char in text.strip().lower())
    normalized = normalized.strip("_")
    return normalized[:48] or "compare"


def _text(language: str, key: str) -> str:
    locale = "en-US" if language == "en-US" else "zh-CN"
    messages = {
        "zh-CN": {
            "recommend_default_baseline": "优先推荐当前会话默认模型结果，便于把多模型对比收敛到稳定基线。",
            "recommend_first_success": "默认推荐首个成功结果，作为 compare 收敛的确定性基线。",
        },
        "en-US": {
            "recommend_default_baseline": "Prefer the current session-default result so compare can converge onto a stable baseline.",
            "recommend_first_success": "Prefer the first successful result as the deterministic fallback baseline for compare review.",
        },
    }
    return messages[locale][key]
