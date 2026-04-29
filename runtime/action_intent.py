"""Action/Effect Boundary — pre-route authorization gate (ADR-017 P0).

Validator 是唯一授权者。Host LLM 生成 ActionProposal，Validator 基于
ActionProposal + ValidationContext 输出统一 ValidationDecision。

P0 只激活 consult_readonly route override；side-effecting action 做最小
evidence proof 授权但不接管路由；未知 action 回落现有 Router。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# -- Action types recognized by P0 -------------------------------------------

ACTION_TYPES = (
    "consult_readonly",
    "propose_plan",
    "execute_existing_plan",
    "modify_files",
    "checkpoint_response",
    "cancel_flow",
)

SIDE_EFFECTS = (
    "none",
    "write_runtime_state",
    "write_plan_package",
    "write_files",
    "execute_command",
)

CONFIDENCE_LEVELS = ("high", "medium", "low")

# Side effects that require positive evidence proof to authorize.
_SIDE_EFFECTING = frozenset(SIDE_EFFECTS) - {"none"}

# -- Validation decision codes ------------------------------------------------

DECISION_AUTHORIZE = "authorize"
DECISION_DOWNGRADE = "downgrade"
DECISION_REJECT = "reject"
DECISION_FALLBACK_ROUTER = "fallback_router"


# -- Data contracts -----------------------------------------------------------


@dataclass(frozen=True)
class ActionProposal:
    """Host-generated structured intent (proposal source, not authorizer)."""

    action_type: str
    side_effect: str = "none"
    confidence: str = "high"
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "side_effect": self.side_effect,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionProposal":
        action_type = str(data.get("action_type") or "").strip()
        side_effect = str(data.get("side_effect") or "none")
        confidence = str(data.get("confidence") or "high")

        # Missing/empty action_type is invalid — fail-close.
        if not action_type:
            raise ValueError("action_type is required and must not be empty")
        # Strict enum validation — reject unknown values at parse time.
        if action_type not in ACTION_TYPES:
            raise ValueError(f"unknown action_type: {action_type!r}")
        if side_effect not in SIDE_EFFECTS:
            raise ValueError(f"unknown side_effect: {side_effect!r}")
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError(f"unknown confidence: {confidence!r}")

        # Evidence must be a list of strings, not a bare string.
        raw_evidence = data.get("evidence")
        if raw_evidence is None:
            evidence: tuple[str, ...] = ()
        elif isinstance(raw_evidence, list):
            if not all(isinstance(e, str) for e in raw_evidence):
                raise ValueError("evidence must be a list of strings")
            evidence = tuple(raw_evidence)
        else:
            raise ValueError(f"evidence must be a list, got {type(raw_evidence).__name__}")

        return cls(
            action_type=action_type,
            side_effect=side_effect,
            confidence=confidence,
            evidence=evidence,
        )


@dataclass(frozen=True)
class ValidationContext:
    """Read-only view projected from context_snapshot / current_handoff / current_run.

    不新造完整模型；只取 Validator 需要的最小字段。
    """

    checkpoint_kind: Optional[str] = None
    checkpoint_id: Optional[str] = None
    stage: Optional[str] = None
    required_host_action: Optional[str] = None


@dataclass(frozen=True)
class ValidationDecision:
    """Validator 统一输出。"""

    decision: str  # authorize | downgrade | reject | fallback_router
    resolved_action: str
    resolved_side_effect: str
    route_override: Optional[str] = None  # "consult" or None
    reason_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "resolved_action": self.resolved_action,
            "resolved_side_effect": self.resolved_side_effect,
            "route_override": self.route_override,
            "reason_code": self.reason_code,
        }


# -- Validator ----------------------------------------------------------------


class ActionValidator:
    """Pre-write authorization gate (Verify-A).

    P0 硬规则：
    - consult_readonly + none → authorize, route_override=consult
    - side-effecting + evidence 通过 → authorize, route_override=None (Router 继续)
    - side-effecting + evidence 不足/low confidence → downgrade consult_readonly
    - 未知 action → fallback_router
    """

    def validate(
        self,
        proposal: ActionProposal,
        context: ValidationContext,
    ) -> ValidationDecision:
        # Unknown action type → fall back to existing Router.
        if proposal.action_type not in ACTION_TYPES:
            return ValidationDecision(
                decision=DECISION_FALLBACK_ROUTER,
                resolved_action=proposal.action_type,
                resolved_side_effect=proposal.side_effect,
                route_override=None,
                reason_code="validator.unknown_action_type",
            )

        # Unknown side_effect → fail-close: downgrade to consult.
        if proposal.side_effect not in SIDE_EFFECTS:
            return ValidationDecision(
                decision=DECISION_DOWNGRADE,
                resolved_action="consult_readonly",
                resolved_side_effect="none",
                route_override="consult",
                reason_code="validator.unknown_side_effect_downgrade",
            )

        # consult_readonly + none: always authorize, regardless of confidence.
        if proposal.action_type == "consult_readonly" and proposal.side_effect == "none":
            return ValidationDecision(
                decision=DECISION_AUTHORIZE,
                resolved_action="consult_readonly",
                resolved_side_effect="none",
                route_override="consult",
                reason_code="validator.consult_readonly_authorized",
            )

        # consult_readonly with unexpected side_effect → treat as side-effecting.
        # (Host claimed readonly but declared write — evidence must prove it.)

        # Side-effecting actions: require confidence + evidence proof.
        if proposal.side_effect in _SIDE_EFFECTING:
            if not _evidence_proves_write_intent(proposal):
                return ValidationDecision(
                    decision=DECISION_DOWNGRADE,
                    resolved_action="consult_readonly",
                    resolved_side_effect="none",
                    route_override="consult",
                    reason_code="validator.insufficient_evidence_downgrade",
                )
            # Evidence sufficient → authorize, let Router decide route.
            return ValidationDecision(
                decision=DECISION_AUTHORIZE,
                resolved_action=proposal.action_type,
                resolved_side_effect=proposal.side_effect,
                route_override=None,
                reason_code="validator.side_effect_authorized",
            )

        # Non-side-effecting recognized action (e.g. cancel_flow with none).
        # Authorize and let Router handle.
        return ValidationDecision(
            decision=DECISION_AUTHORIZE,
            resolved_action=proposal.action_type,
            resolved_side_effect=proposal.side_effect,
            route_override=None,
            reason_code="validator.action_authorized",
        )


def _evidence_proves_write_intent(proposal: ActionProposal) -> bool:
    """P0 最小 evidence proof: confidence 不能是 low，且 evidence 非空。

    判定标准是"evidence 能否正向证明写入意图"，不列举具体话术词表。
    fail-close: 允许误降级为 consult，不允许误升级为写入。
    """
    if proposal.confidence == "low":
        return False
    if not proposal.evidence:
        return False
    return True


# -- Deterministic fallback adapter -------------------------------------------


def resolve_action_proposal(
    raw_json: Optional[dict[str, Any]],
) -> Optional[ActionProposal]:
    """Parse raw JSON into ActionProposal, or None if absent/invalid.

    None 表示无 proposal — engine 应回落现有 Router。
    """
    if raw_json is None:
        return None
    try:
        return ActionProposal.from_dict(raw_json)
    except (TypeError, KeyError, ValueError, AttributeError):
        return None
