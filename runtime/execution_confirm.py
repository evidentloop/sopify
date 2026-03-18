"""Execution-confirm helpers for the plan-to-develop handoff."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .models import ExecutionSummary, PlanArtifact, RuntimeConfig

_STATUS_ALIASES = {
    "查看执行确认",
    "查看当前方案",
    "查看当前计划",
    "status",
    "show execution confirmation",
}
_CONFIRM_ALIASES = {
    "继续",
    "继续执行",
    "下一步",
    "开始",
    "开始执行",
    "开工",
    "resume",
    "continue",
    "next",
    "start",
    "begin",
    "yes",
    "ok",
}
_CANCEL_ALIASES = {"取消", "停止", "终止", "abort", "cancel", "stop"}
_TASK_RE = re.compile(r"^- \[(?: |x|!|-)\]\s+", re.MULTILINE)
_RISK_LEVEL_KEYWORDS = {
    "high": ("认证", "授权", "auth", "schema", "migration", "删除", "drop", "truncate", "权限"),
    "medium": ("边界", "兼容", "回滚", "rollback", "范围", "scope", "tradeoff", "trade-off"),
}


@dataclass(frozen=True)
class ExecutionConfirmResponse:
    """Normalized interpretation of a pre-execution confirmation reply."""

    action: str
    feedback: str = ""
    message: str = ""


def parse_execution_confirm_response(user_input: str) -> ExecutionConfirmResponse:
    """Interpret a raw user response while waiting for execution confirmation."""
    text = user_input.strip()
    if not text:
        return ExecutionConfirmResponse(action="invalid", message="Empty execution confirmation response")

    normalized = _normalize(text)
    if normalized in {alias.casefold() for alias in _STATUS_ALIASES}:
        return ExecutionConfirmResponse(action="status")
    if normalized in {alias.casefold() for alias in _CONFIRM_ALIASES}:
        return ExecutionConfirmResponse(action="confirm")
    if normalized in {alias.casefold() for alias in _CANCEL_ALIASES}:
        return ExecutionConfirmResponse(action="cancel")
    return ExecutionConfirmResponse(action="revise", feedback=text)


def build_execution_summary(*, plan_artifact: PlanArtifact, config: RuntimeConfig) -> ExecutionSummary:
    """Build the minimum plan summary required before execution."""
    plan_dir = config.workspace_root / plan_artifact.path
    task_text = _read_first_existing(plan_dir, "tasks.md", "plan.md")
    risk_text = _read_first_existing(plan_dir, "background.md", "plan.md", "design.md")

    key_risk = _extract_prefixed_line(risk_text, "- 风险:", "- Risk:") or _default_risk(config.language)
    mitigation = _extract_prefixed_line(risk_text, "- 缓解:", "- Mitigation:") or _default_mitigation(config.language)
    return ExecutionSummary(
        plan_path=plan_artifact.path,
        summary=plan_artifact.summary,
        task_count=len(_TASK_RE.findall(task_text)),
        risk_level=_infer_risk_level(key_risk, mitigation),
        key_risk=key_risk,
        mitigation=mitigation,
    )


def _read_first_existing(plan_dir: Path, *filenames: str) -> str:
    for filename in filenames:
        candidate = plan_dir / filename
        if candidate.exists() and candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    return ""


def _extract_prefixed_line(text: str, *prefixes: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        for prefix in prefixes:
            if stripped.casefold().startswith(prefix.casefold()):
                return stripped[len(prefix) :].strip()
    return ""


def _infer_risk_level(key_risk: str, mitigation: str) -> str:
    aggregate_text = f"{key_risk}\n{mitigation}".casefold()
    for level, keywords in _RISK_LEVEL_KEYWORDS.items():
        if any(keyword.casefold() in aggregate_text for keyword in keywords):
            return level
    return "low"


def _default_risk(language: str) -> str:
    if language == "en-US":
        return "No standalone risk was recorded; execution should still stay within the documented scope."
    return "当前未单独记录额外风险，执行时仍需严格约束在已确认范围内。"


def _default_mitigation(language: str) -> str:
    if language == "en-US":
        return "Keep the change minimal, re-check the file scope, and finish with focused verification."
    return "保持最小改动，复核文件范围，并在收口前完成针对性验证。"


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())
