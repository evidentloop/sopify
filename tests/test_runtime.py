from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.config import ConfigError, load_runtime_config
from runtime.clarification_bridge import (
    build_cli_clarification_bridge,
    load_clarification_bridge_context,
    prompt_cli_clarification_submission,
)
from runtime.compare_decision import build_compare_decision_contract
from runtime.decision import build_execution_gate_decision_state, confirm_decision, response_from_submission
from runtime.decision_bridge import (
    DecisionBridgeContext,
    build_cli_decision_bridge,
    prompt_cli_decision_submission,
)
from runtime.decision_policy import match_decision_policy
from runtime.decision_templates import CUSTOM_OPTION_ID, PRIMARY_OPTION_FIELD_ID, build_strategy_pick_template
from runtime.engine import run_runtime
from runtime.execution_gate import evaluate_execution_gate
from runtime.kb import bootstrap_kb
from runtime.plan_scaffold import create_plan_scaffold
from runtime.output import render_runtime_output
from runtime.replay import ReplayWriter, build_decision_replay_event
from runtime.router import Router
from runtime.skill_registry import SkillRegistry
from runtime.state import StateStore, iso_now
from runtime.models import (
    DecisionCheckpoint,
    DecisionCondition,
    DecisionField,
    DecisionOption,
    DecisionRecommendation,
    DecisionSelection,
    DecisionState,
    DecisionSubmission,
    DecisionValidation,
    PlanArtifact,
    ReplayEvent,
    RouteDecision,
    RunState,
)
from scripts.model_compare_runtime import make_default_candidate


class _FakeInteractiveSession:
    def __init__(self, *, single_choice: object = None, multi_choice: list[object] | None = None, confirm_value: bool = True) -> None:
        self.single_choice = single_choice
        self.multi_choice = list(multi_choice or [])
        self.confirm_value = confirm_value

    def is_available(self) -> bool:
        return True

    def select(self, *, title: str, items, instructions: str, initial_value=None):
        return self.single_choice if self.single_choice is not None else list(items)[0]["value"]

    def multi_select(self, *, title: str, items, instructions: str, initial_values=(), required: bool = False):
        if self.multi_choice:
            return list(self.multi_choice)
        if required:
            return [list(items)[0]["value"]]
        return list(initial_values)

    def confirm(self, *, title: str, yes_label: str, no_label: str, default_value=None, instructions: str) -> bool:
        return self.confirm_value


def _rewrite_background_scope(
    workspace: Path,
    plan_artifact: PlanArtifact,
    *,
    scope_lines: tuple[str, str],
    risk_lines: tuple[str, str] | None = None,
) -> None:
    background_path = workspace / plan_artifact.path / "background.md"
    text = background_path.read_text(encoding="utf-8")
    text = text.replace(
        "- 模块: 待分析\n- 文件: 待分析",
        f"- 模块: {scope_lines[0]}\n- 文件: {scope_lines[1]}",
    )
    if risk_lines is not None:
        text = re.sub(
            r"- 风险: .+\n- 缓解: .+",
            f"- 风险: {risk_lines[0]}\n- 缓解: {risk_lines[1]}",
            text,
        )
    background_path.write_text(text, encoding="utf-8")


def _prepare_ready_plan_state(
    workspace: Path,
    *,
    request_text: str = "补 runtime 骨架",
) -> tuple[object, StateStore, PlanArtifact]:
    config = load_runtime_config(workspace)
    store = StateStore(config)
    store.ensure()
    plan_artifact = create_plan_scaffold(request_text, config=config, level="standard")
    _rewrite_background_scope(
        workspace,
        plan_artifact,
        scope_lines=("runtime/router.py, runtime/engine.py", "runtime/router.py, runtime/engine.py, tests/test_runtime.py"),
        risk_lines=("需要确保执行前确认不会误触发 develop", "统一通过 execution_confirm_pending 与 gate ready 再进入执行"),
    )
    gate = evaluate_execution_gate(
        decision=RouteDecision(
            route_name="workflow",
            request_text=request_text,
            reason="test",
            complexity="complex",
            plan_level="standard",
            candidate_skill_ids=("develop",),
        ),
        plan_artifact=plan_artifact,
        current_clarification=None,
        current_decision=None,
        config=config,
    )
    store.set_current_plan(plan_artifact)
    store.set_current_run(
        RunState(
            run_id="run-ready",
            status="active",
            stage="ready_for_execution",
            route_name="workflow",
            title=plan_artifact.title,
            created_at=iso_now(),
            updated_at=iso_now(),
            plan_id=plan_artifact.plan_id,
            plan_path=plan_artifact.path,
            execution_gate=gate,
        )
    )
    return config, store, plan_artifact


class RuntimeConfigTests(unittest.TestCase):
    def test_zero_config_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = load_runtime_config(temp_dir, global_config_path=Path(temp_dir) / "missing.yaml")
            self.assertEqual(config.language, "zh-CN")
            self.assertEqual(config.workflow_mode, "adaptive")
            self.assertEqual(config.plan_directory, ".sopify-skills")
            self.assertFalse(config.multi_model_enabled)
            self.assertTrue(config.brand.endswith("-ai"))

    def test_project_config_overrides_global(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            global_path = workspace / "global.yaml"
            project_path = workspace / "sopify.config.yaml"
            global_path.write_text(
                "language: en-US\nworkflow:\n  require_score: 5\nplan:\n  level: light\n",
                encoding="utf-8",
            )
            project_path.write_text(
                "workflow:\n  require_score: 9\nplan:\n  directory: .runtime\n",
                encoding="utf-8",
            )
            config = load_runtime_config(workspace, global_config_path=global_path)
            self.assertEqual(config.language, "en-US")
            self.assertEqual(config.require_score, 9)
            self.assertEqual(config.plan_level, "light")
            self.assertEqual(config.plan_directory, ".runtime")

    def test_invalid_config_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "sopify.config.yaml").write_text("workflow:\n  mode: unsupported\n", encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_runtime_config(workspace)

    def test_brand_auto_prefers_package_name_over_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "package.json").write_text('{"name":"sample-workspace"}', encoding="utf-8")
            config = load_runtime_config(workspace, global_config_path=workspace / "missing.yaml")
            self.assertEqual(config.brand, "sample-workspace-ai")


class RouterTests(unittest.TestCase):
    def test_route_classification_and_active_flow_intents(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)
            store = StateStore(config)
            store.ensure()
            router = Router(config, state_store=store)
            skills = SkillRegistry(config, user_home=workspace / "home").discover()

            plan_route = router.classify("~go plan 补 runtime 骨架", skills=skills)
            finalize_route = router.classify("~go finalize", skills=skills)
            self.assertEqual(plan_route.route_name, "plan_only")
            self.assertTrue(plan_route.should_create_plan)
            self.assertEqual(finalize_route.route_name, "finalize_active")
            self.assertTrue(finalize_route.should_recover_context)

            run_state = RunState(
                run_id="run-1",
                status="active",
                stage="plan_ready",
                route_name="workflow",
                title="Runtime",
                created_at=iso_now(),
                updated_at=iso_now(),
            )
            store.set_current_run(run_state)
            resume_route = router.classify("继续", skills=skills)
            cancel_route = router.classify("取消", skills=skills)
            replay_route = router.classify("回放最近一次实现", skills=skills)
            compare_route = router.classify("~compare 方案对比", skills=skills)
            consult_route = router.classify("这个方案为什么要这样拆？", skills=skills)

            self.assertEqual(resume_route.route_name, "resume_active")
            self.assertTrue(resume_route.should_recover_context)
            self.assertEqual(cancel_route.route_name, "cancel_active")
            self.assertEqual(replay_route.route_name, "replay")
            self.assertEqual(compare_route.route_name, "compare")
            self.assertEqual(consult_route.route_name, "consult")

    def test_ready_plan_routes_continue_and_exec_into_execution_confirm(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config, store, _ = _prepare_ready_plan_state(workspace)
            router = Router(config, state_store=store)
            skills = SkillRegistry(config, user_home=workspace / "home").discover()

            continue_route = router.classify("继续", skills=skills)
            exec_route = router.classify("~go exec", skills=skills)
            revise_route = router.classify("先把风险部分再展开一点", skills=skills)

            self.assertEqual(continue_route.route_name, "execution_confirm_pending")
            self.assertEqual(continue_route.active_run_action, "confirm_execution")
            self.assertEqual(exec_route.route_name, "execution_confirm_pending")
            self.assertEqual(exec_route.active_run_action, "inspect_execution_confirm")
            self.assertEqual(revise_route.route_name, "execution_confirm_pending")
            self.assertEqual(revise_route.active_run_action, "revise_execution")

    def test_pending_clarification_intercepts_exec_and_accepts_answers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)
            store = StateStore(config)
            store.ensure()
            router = Router(config, state_store=store)
            skills = SkillRegistry(config, user_home=workspace / "home").discover()

            run_runtime("~go plan 优化一下", workspace_root=workspace, user_home=workspace / "home")

            blocked_exec = router.classify("~go exec", skills=skills)
            answer = router.classify("目标是 runtime/router.py，预期结果是补状态骨架", skills=skills)

            self.assertEqual(blocked_exec.route_name, "clarification_pending")
            self.assertEqual(answer.route_name, "clarification_resume")

    def test_pending_clarification_submission_routes_to_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)
            store = StateStore(config)
            store.ensure()
            router = Router(config, state_store=store)
            skills = SkillRegistry(config, user_home=workspace / "home").discover()

            run_runtime("~go plan 优化一下", workspace_root=workspace, user_home=workspace / "home")

            store = StateStore(load_runtime_config(workspace))
            store.set_current_clarification_response(
                response_text="目标范围：runtime/router.py\n预期结果：补结构化 clarification bridge。",
                response_fields={
                    "target_scope": "runtime/router.py",
                    "expected_outcome": "补结构化 clarification bridge。",
                },
                response_source="cli",
                response_message="host form submitted",
            )

            resumed = router.classify("继续", skills=skills)

            self.assertEqual(resumed.route_name, "clarification_resume")
            self.assertEqual(resumed.active_run_action, "clarification_response_from_state")

    def test_pending_decision_intercepts_exec_until_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)
            store = StateStore(config)
            store.ensure()
            router = Router(config, state_store=store)
            skills = SkillRegistry(config, user_home=workspace / "home").discover()

            run_runtime(
                "~go plan payload 放 host root 还是 workspace/.sopify-runtime",
                workspace_root=workspace,
                user_home=workspace / "home",
            )

            blocked_exec = router.classify("~go exec", skills=skills)
            self.assertEqual(blocked_exec.route_name, "decision_pending")
            self.assertEqual(blocked_exec.active_run_action, "inspect_decision")

    def test_pending_decision_submission_routes_to_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)
            store = StateStore(config)
            store.ensure()
            router = Router(config, state_store=store)
            skills = SkillRegistry(config, user_home=workspace / "home").discover()

            run_runtime(
                "~go plan payload 放 host root 还是 workspace/.sopify-runtime",
                workspace_root=workspace,
                user_home=workspace / "home",
            )
            store.set_current_decision_submission(
                DecisionSubmission(
                    status="submitted",
                    source="cli",
                    answers={"selected_option_id": "option_1"},
                    submitted_at=iso_now(),
                    resume_action="submit",
                )
            )

            resumed = router.classify("继续", skills=skills)

            self.assertEqual(resumed.route_name, "decision_resume")
            self.assertEqual(resumed.active_run_action, "resume_submitted_decision")


class DecisionContractTests(unittest.TestCase):
    def test_decision_policy_keeps_current_planning_semantic_baseline(self) -> None:
        route = RouteDecision(
            route_name="plan_only",
            request_text="payload 放 host root 还是 workspace/.sopify-runtime",
            reason="test",
            complexity="complex",
            plan_level="standard",
        )

        match = match_decision_policy(route)

        self.assertIsNotNone(match)
        self.assertEqual(match.template_id, "strategy_pick")
        self.assertEqual(match.decision_type, "architecture_choice")
        self.assertEqual(match.option_texts, ("payload 放 host root", "workspace/.sopify-runtime"))

    def test_decision_policy_ignores_non_architecture_alternatives(self) -> None:
        route = RouteDecision(
            route_name="workflow",
            request_text="按钮改红色还是蓝色",
            reason="test",
            complexity="complex",
            plan_level="standard",
        )

        self.assertIsNone(match_decision_policy(route))

    def test_decision_policy_prefers_structured_tradeoff_candidates(self) -> None:
        route = RouteDecision(
            route_name="workflow",
            request_text="重构支付模块",
            reason="test",
            complexity="complex",
            plan_level="standard",
            artifacts={
                "decision_question": "确认支付模块改造路径",
                "decision_summary": "存在两个可执行方案，需要先确认长期方向。",
                "decision_context_files": [
                    ".sopify-skills/blueprint/design.md",
                    ".sopify-skills/project.md",
                ],
                "decision_candidates": [
                    {
                        "id": "incremental",
                        "title": "渐进改造",
                        "summary": "低风险拆分现有支付链路。",
                        "tradeoffs": ["迁移周期更长"],
                        "impacts": ["兼容当前发布节奏"],
                    },
                    {
                        "id": "rewrite",
                        "title": "整体重写",
                        "summary": "统一支付边界与数据模型。",
                        "tradeoffs": ["一次性变更面更大"],
                        "impacts": ["长期一致性更强"],
                        "recommended": True,
                    },
                ],
            },
        )

        match = match_decision_policy(route)

        self.assertIsNotNone(match)
        self.assertEqual(match.policy_id, "design_tradeoff_candidates")
        self.assertEqual(match.question, "确认支付模块改造路径")
        self.assertEqual(match.context_files, (".sopify-skills/blueprint/design.md", ".sopify-skills/project.md"))
        self.assertEqual(match.options[1].option_id, "rewrite")
        self.assertEqual(match.recommended_option_index, 1)

    def test_decision_policy_suppresses_structured_tradeoff_when_preference_locked(self) -> None:
        route = RouteDecision(
            route_name="workflow",
            request_text="重构支付模块",
            reason="test",
            complexity="complex",
            plan_level="standard",
            artifacts={
                "decision_preference_locked": True,
                "decision_candidates": [
                    {"id": "option_1", "title": "方案一", "summary": "低风险", "tradeoffs": ["慢"]},
                    {"id": "option_2", "title": "方案二", "summary": "高一致性", "tradeoffs": ["快但风险高"]},
                ],
            },
        )

        self.assertIsNone(match_decision_policy(route))

    def test_strategy_pick_template_supports_custom_and_constraint_fields(self) -> None:
        rendered = build_strategy_pick_template(
            checkpoint_id="decision_template_1",
            question="确认方案",
            summary="请选择本轮方向",
            options=(
                DecisionOption(option_id="option_1", title="方案一", summary="保守路径", recommended=True),
                DecisionOption(option_id="option_2", title="方案二", summary="激进路径"),
            ),
            language="zh-CN",
            recommended_option_id="option_1",
            default_option_id="option_1",
            allow_custom_option=True,
            constraint_field_type="input",
        )

        self.assertEqual(len(rendered.options), 3)
        self.assertEqual(rendered.options[-1].option_id, CUSTOM_OPTION_ID)
        self.assertEqual(len(rendered.checkpoint.fields), 3)
        self.assertEqual(rendered.checkpoint.fields[0].field_id, PRIMARY_OPTION_FIELD_ID)
        self.assertEqual(rendered.checkpoint.fields[1].field_type, "textarea")
        self.assertEqual(rendered.checkpoint.fields[1].when[0].value, CUSTOM_OPTION_ID)
        self.assertEqual(rendered.checkpoint.fields[2].field_type, "input")

    def test_compare_decision_contract_shortlists_successful_results(self) -> None:
        contract = build_compare_decision_contract(
            question="比较支付模块重构方案",
            language="zh-CN",
            skill_result={
                "results": [
                    {"candidate_id": "session_default", "status": "ok", "answer": "建议先做渐进拆分。", "latency_ms": 120},
                    {"candidate_id": "external_a", "status": "ok", "answer": "建议整体重写，但要补迁移预案。", "latency_ms": 220},
                    {"candidate_id": "external_b", "status": "error", "error": "boom", "latency_ms": 10},
                    {"candidate_id": "external_c", "status": "ok", "answer": "建议先统一接口，再逐步迁移数据。", "latency_ms": 180},
                ]
            },
        )

        self.assertIsNotNone(contract)
        self.assertEqual(contract["decision_type"], "compare_result_choice")
        self.assertEqual(contract["recommended_option_id"], "session_default")
        self.assertEqual(contract["result_count"], 3)
        self.assertEqual(contract["shortlisted_result_count"], 3)
        checkpoint = contract["checkpoint"]
        self.assertEqual(checkpoint["primary_field_id"], PRIMARY_OPTION_FIELD_ID)
        self.assertEqual(checkpoint["recommendation"]["option_id"], "session_default")
        self.assertIn("session_default", [item["id"] for item in checkpoint["fields"][0]["options"]])

    def test_cli_decision_bridge_exposes_interactive_contract_and_text_fallback(self) -> None:
        rendered = build_strategy_pick_template(
            checkpoint_id="decision_template_cli",
            question="确认方案",
            summary="请选择本轮方向",
            options=(
                DecisionOption(option_id="option_1", title="方案一", summary="保守路径", recommended=True),
                DecisionOption(option_id="option_2", title="方案二", summary="激进路径"),
            ),
            language="zh-CN",
            recommended_option_id="option_1",
            default_option_id="option_1",
            allow_custom_option=True,
            constraint_field_type="confirm",
        )
        context = DecisionBridgeContext(
            handoff=None,
            decision_state=DecisionState(
                schema_version="2",
                decision_id="decision_template_cli",
                feature_key="decision",
                phase="design",
                status="pending",
                decision_type="architecture_choice",
                question="确认方案",
                summary="请选择本轮方向",
                options=rendered.options,
                checkpoint=rendered.checkpoint,
                recommended_option_id=rendered.recommended_option_id,
                default_option_id=rendered.default_option_id,
            ),
            checkpoint=rendered.checkpoint,
            submission_state={"status": "empty", "has_answers": False, "answer_keys": []},
        )

        bridge = build_cli_decision_bridge(context, language="zh-CN")

        self.assertEqual(bridge["host_kind"], "cli")
        self.assertEqual(bridge["presentation"]["recommended_mode"], "interactive_form")
        self.assertEqual(bridge["steps"][0]["renderer"], "cli.select")
        self.assertEqual(bridge["steps"][0]["fallback_renderer"], "text")
        self.assertEqual(bridge["steps"][1]["ui_kind"], "textarea")
        self.assertEqual(bridge["steps"][1]["fallback_renderer"], "text")
        self.assertEqual(bridge["steps"][2]["ui_kind"], "confirm")

    def test_decision_checkpoint_roundtrip_normalizes_contract_fields(self) -> None:
        checkpoint = DecisionCheckpoint(
            checkpoint_id="decision_contract_1",
            title="选择方案",
            message="请选择最终执行路径",
            fields=(
                DecisionField(
                    field_id="selected_option_id",
                    field_type="select",
                    label="方案",
                    required=True,
                    options=(
                        DecisionOption(option_id="option_1", title="方案一", summary="保守路径", recommended=True),
                        DecisionOption(option_id="option_2", title="方案二", summary="激进路径"),
                    ),
                    validations=(DecisionValidation(rule="required", message="必须选择一个方案"),),
                ),
                DecisionField(
                    field_id="custom_reason",
                    field_type="textarea",
                    label="补充说明",
                    when=(DecisionCondition(field_id="selected_option_id", operator="not_in", value=["option_1"]),),
                ),
            ),
            primary_field_id="selected_option_id",
            recommendation=DecisionRecommendation(
                field_id="selected_option_id",
                option_id="option_1",
                summary="默认推荐方案一",
                reason="风险最低",
            ),
        )

        payload = checkpoint.to_dict()
        payload["fields"][0]["field_type"] = "SELECT"
        payload["fields"][1]["field_type"] = "TEXTAREA"
        payload["fields"][1]["when"][0]["operator"] = "NOT-IN"
        restored = DecisionCheckpoint.from_dict(payload)

        self.assertEqual(restored.fields[0].field_type, "select")
        self.assertEqual(restored.fields[1].field_type, "textarea")
        self.assertEqual(restored.fields[1].when[0].operator, "not_in")
        self.assertEqual(restored.recommendation.option_id, "option_1")

    def test_state_store_persists_structured_submission(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run_runtime(
                "~go plan payload 放 host root 还是 workspace/.sopify-runtime",
                workspace_root=workspace,
                user_home=workspace / "home",
            )

            store = StateStore(load_runtime_config(workspace))
            updated = store.set_current_decision_submission(
                DecisionSubmission(
                    status="collecting",
                    source="cli",
                    answers={"selected_option_id": "option_2"},
                    submitted_at=iso_now(),
                    resume_action="submit",
                )
            )

            self.assertIsNotNone(updated)
            self.assertEqual(updated.status, "collecting")
            reloaded = store.get_current_decision()
            self.assertEqual(reloaded.status, "collecting")
            self.assertEqual(reloaded.submission.answers["selected_option_id"], "option_2")

    def test_response_from_submission_uses_legacy_answer_key_fallback(self) -> None:
        decision_state = DecisionState(
            schema_version="2",
            decision_id="decision_submission_1",
            feature_key="decision",
            phase="design",
            status="pending",
            decision_type="architecture_choice",
            question="确认方案",
            summary="请选择方向",
            options=(
                DecisionOption(option_id="option_1", title="方案一", summary="保守路径", recommended=True),
                DecisionOption(option_id="option_2", title="方案二", summary="激进路径"),
            ),
            checkpoint=DecisionCheckpoint(
                checkpoint_id="decision_submission_1",
                title="确认方案",
                message="请选择方向",
                fields=(),
                primary_field_id=None,
            ),
            submission=DecisionSubmission(
                status="submitted",
                source="cli",
                answers={"selected_option_id": "option_2"},
                submitted_at=iso_now(),
                resume_action="submit",
            ),
        )

        response = response_from_submission(decision_state)

        self.assertIsNotNone(response)
        self.assertEqual(response.action, "choose")
        self.assertEqual(response.option_id, "option_2")

    def test_handoff_includes_decision_checkpoint_and_submission_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            pending = run_runtime(
                "~go plan payload 放 host root 还是 workspace/.sopify-runtime",
                workspace_root=workspace,
                user_home=workspace / "home",
            )
            self.assertIn("decision_checkpoint", pending.handoff.artifacts)
            self.assertEqual(pending.handoff.artifacts["decision_submission_state"]["status"], "empty")

            store = StateStore(load_runtime_config(workspace))
            store.set_current_decision_submission(
                DecisionSubmission(
                    status="submitted",
                    source="cli",
                    answers={"selected_option_id": "option_1"},
                    submitted_at=iso_now(),
                    resume_action="submit",
                )
            )

            inspected = run_runtime("~decide status", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(inspected.route.route_name, "decision_pending")
            self.assertEqual(inspected.handoff.artifacts["decision_checkpoint"]["primary_field_id"], "selected_option_id")
            self.assertEqual(inspected.handoff.artifacts["decision_submission_state"]["status"], "submitted")
            self.assertEqual(inspected.handoff.artifacts["decision_submission_state"]["answer_keys"], ["selected_option_id"])

    def test_cli_text_bridge_collects_submission_and_runtime_can_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run_runtime(
                "~go plan payload 放 host root 还是 workspace/.sopify-runtime",
                workspace_root=workspace,
                user_home=workspace / "home",
            )
            config = load_runtime_config(workspace)
            answers = iter(("1",))

            submission, used_renderer = prompt_cli_decision_submission(
                config=config,
                renderer="auto",
                input_reader=lambda _prompt: next(answers),
                output_writer=lambda _message: None,
            )

            self.assertEqual(used_renderer, "text")
            self.assertEqual(submission.answers["selected_option_id"], "option_1")
            store = StateStore(config)
            updated = store.get_current_decision()
            self.assertIsNotNone(updated)
            self.assertEqual(updated.submission.status, "submitted")
            self.assertEqual(updated.submission.answers["selected_option_id"], "option_1")

            resumed = run_runtime("继续", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(resumed.route.route_name, "plan_only")
            self.assertIsNotNone(resumed.plan_artifact)
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_decision.json").exists())

    def test_cli_interactive_bridge_collects_submission_without_text_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run_runtime(
                "~go plan payload 放 host root 还是 workspace/.sopify-runtime",
                workspace_root=workspace,
                user_home=workspace / "home",
            )
            config = load_runtime_config(workspace)

            submission, used_renderer = prompt_cli_decision_submission(
                config=config,
                renderer="interactive",
                input_reader=lambda _prompt: "",
                output_writer=lambda _message: None,
                interactive_session_factory=lambda: _FakeInteractiveSession(single_choice="option_2"),
            )

            self.assertEqual(used_renderer, "interactive")
            self.assertEqual(submission.answers["selected_option_id"], "option_2")
            self.assertEqual(submission.source, "cli_interactive")

    def test_decision_bridge_script_inspect_and_submit_for_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run_runtime(
                "~go plan payload 放 host root 还是 workspace/.sopify-runtime",
                workspace_root=workspace,
                user_home=workspace / "home",
            )
            script_path = REPO_ROOT / "scripts" / "decision_bridge_runtime.py"

            inspected = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--workspace-root",
                    str(workspace),
                    "inspect",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(inspected.returncode, 0, msg=inspected.stderr)
            inspect_payload = json.loads(inspected.stdout)
            self.assertEqual(inspect_payload["status"], "ready")
            self.assertEqual(inspect_payload["bridge"]["host_kind"], "cli")
            self.assertEqual(inspect_payload["bridge"]["steps"][0]["renderer"], "cli.select")

            submitted = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--workspace-root",
                    str(workspace),
                    "submit",
                    "--answers-json",
                    '{"selected_option_id":"option_1"}',
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(submitted.returncode, 0, msg=submitted.stderr)
            submit_payload = json.loads(submitted.stdout)
            self.assertEqual(submit_payload["status"], "written")
            self.assertEqual(submit_payload["submission"]["answers"]["selected_option_id"], "option_1")

            store = StateStore(load_runtime_config(workspace))
            updated = store.get_current_decision()
            self.assertIsNotNone(updated)
            self.assertEqual(updated.submission.status, "submitted")
            self.assertEqual(updated.submission.answers["selected_option_id"], "option_1")

    def test_cli_clarification_bridge_exposes_interactive_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run_runtime("~go plan 优化一下", workspace_root=workspace, user_home=workspace / "home")
            config = load_runtime_config(workspace)

            context = load_clarification_bridge_context(config=config)
            bridge = build_cli_clarification_bridge(context, language="zh-CN")

            self.assertEqual(bridge["host_kind"], "cli")
            self.assertEqual(bridge["required_host_action"], "answer_questions")
            self.assertEqual(bridge["presentation"]["recommended_mode"], "interactive_form")
            self.assertEqual([step["field_id"] for step in bridge["steps"]], ["target_scope", "expected_outcome"])
            self.assertEqual(bridge["steps"][0]["renderer"], "cli.input")
            self.assertEqual(bridge["steps"][1]["fallback_renderer"], "text")

    def test_cli_clarification_bridge_collects_submission_and_runtime_can_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run_runtime("~go plan 优化一下", workspace_root=workspace, user_home=workspace / "home")
            config = load_runtime_config(workspace)
            answers = iter(("runtime/router.py", "补结构化 clarification bridge。", "."))

            submission, used_renderer = prompt_cli_clarification_submission(
                config=config,
                renderer="auto",
                input_reader=lambda _prompt: next(answers),
                output_writer=lambda _message: None,
            )

            self.assertEqual(used_renderer, "text")
            self.assertEqual(submission["response_fields"]["target_scope"], "runtime/router.py")
            self.assertIn("预期结果", submission["response_text"])
            store = StateStore(config)
            updated = store.get_current_clarification()
            self.assertIsNotNone(updated)
            self.assertEqual(updated.response_source, "cli_text")
            self.assertEqual(updated.response_fields["expected_outcome"], "补结构化 clarification bridge。")

            resumed = run_runtime("继续", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(resumed.route.route_name, "plan_only")
            self.assertIsNotNone(resumed.plan_artifact)
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_clarification.json").exists())

    def test_clarification_bridge_script_inspect_and_submit_for_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run_runtime("~go plan 优化一下", workspace_root=workspace, user_home=workspace / "home")
            script_path = REPO_ROOT / "scripts" / "clarification_bridge_runtime.py"

            inspected = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--workspace-root",
                    str(workspace),
                    "inspect",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(inspected.returncode, 0, msg=inspected.stderr)
            inspect_payload = json.loads(inspected.stdout)
            self.assertEqual(inspect_payload["status"], "ready")
            self.assertEqual(inspect_payload["bridge"]["host_kind"], "cli")
            self.assertEqual(inspect_payload["bridge"]["presentation"]["recommended_mode"], "interactive_form")

            submitted = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--workspace-root",
                    str(workspace),
                    "submit",
                    "--answers-json",
                    '{"target_scope":"runtime/router.py","expected_outcome":"补结构化 clarification bridge。"}',
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(submitted.returncode, 0, msg=submitted.stderr)
            submit_payload = json.loads(submitted.stdout)
            self.assertEqual(submit_payload["status"], "written")
            self.assertEqual(submit_payload["submission"]["response_fields"]["target_scope"], "runtime/router.py")

            store = StateStore(load_runtime_config(workspace))
            updated = store.get_current_clarification()
            self.assertIsNotNone(updated)
            self.assertEqual(updated.response_source, "cli")
            self.assertEqual(updated.response_fields["expected_outcome"], "补结构化 clarification bridge。")


class PlanScaffoldTests(unittest.TestCase):
    def test_plan_scaffold_creates_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)

            light = create_plan_scaffold("修复登录错误提示", config=config, level="light")
            standard = create_plan_scaffold("实现 runtime skeleton", config=config, level="standard")
            full = create_plan_scaffold("设计 runtime architecture plugin bridge", config=config, level="full")

            self.assertTrue((workspace / light.path / "plan.md").exists())
            self.assertTrue((workspace / standard.path / "background.md").exists())
            self.assertTrue((workspace / standard.path / "design.md").exists())
            self.assertTrue((workspace / standard.path / "tasks.md").exists())
            self.assertTrue((workspace / full.path / "adr").is_dir())
            self.assertTrue((workspace / full.path / "diagrams").is_dir())

    def test_plan_scaffold_avoids_directory_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)

            first = create_plan_scaffold("补 runtime 骨架", config=config, level="standard")
            second = create_plan_scaffold("补 runtime 骨架", config=config, level="standard")

            self.assertNotEqual(first.path, second.path)
            self.assertTrue(second.path.endswith("-2"))


class ExecutionGateTests(unittest.TestCase):
    def test_execution_gate_blocks_scaffold_until_scope_is_concrete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)
            plan_artifact = create_plan_scaffold("实现 runtime skeleton", config=config, level="standard")
            route = RouteDecision(
                route_name="workflow",
                request_text="实现 runtime skeleton",
                reason="test",
                complexity="complex",
                plan_level="standard",
            )

            gate = evaluate_execution_gate(
                decision=route,
                plan_artifact=plan_artifact,
                current_clarification=None,
                current_decision=None,
                config=config,
            )

            self.assertEqual(gate.gate_status, "blocked")
            self.assertEqual(gate.blocking_reason, "missing_info")
            self.assertEqual(gate.plan_completion, "incomplete")
            self.assertEqual(gate.next_required_action, "continue_host_develop")

    def test_execution_gate_marks_complete_plan_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)
            plan_artifact = create_plan_scaffold("实现 runtime skeleton", config=config, level="standard")
            _rewrite_background_scope(
                workspace,
                plan_artifact,
                scope_lines=("runtime/router.py, runtime/engine.py", "runtime/router.py, runtime/engine.py, tests/test_runtime.py"),
            )
            route = RouteDecision(
                route_name="workflow",
                request_text="实现 runtime skeleton",
                reason="test",
                complexity="complex",
                plan_level="standard",
            )

            gate = evaluate_execution_gate(
                decision=route,
                plan_artifact=plan_artifact,
                current_clarification=None,
                current_decision=None,
                config=config,
            )

            self.assertEqual(gate.gate_status, "ready")
            self.assertEqual(gate.blocking_reason, "none")
            self.assertEqual(gate.plan_completion, "complete")
            self.assertEqual(gate.next_required_action, "confirm_execute")

    def test_execution_gate_requires_decision_for_auth_boundary_risk(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)
            plan_artifact = create_plan_scaffold("调整 auth boundary", config=config, level="standard")
            _rewrite_background_scope(
                workspace,
                plan_artifact,
                scope_lines=("runtime/engine.py", "runtime/engine.py, runtime/router.py"),
                risk_lines=("本轮会调整认证与权限边界", "需要先明确批准路径"),
            )
            route = RouteDecision(
                route_name="workflow",
                request_text="调整 auth boundary",
                reason="test",
                complexity="complex",
                plan_level="standard",
            )

            gate = evaluate_execution_gate(
                decision=route,
                plan_artifact=plan_artifact,
                current_clarification=None,
                current_decision=None,
                config=config,
            )

            self.assertEqual(gate.gate_status, "decision_required")
            self.assertEqual(gate.blocking_reason, "auth_boundary")
            self.assertEqual(gate.plan_completion, "complete")
            self.assertEqual(gate.next_required_action, "confirm_decision")


class ReplayWriterTests(unittest.TestCase):
    def test_replay_writer_creates_append_only_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)
            writer = ReplayWriter(config)
            event = ReplayEvent(
                ts=iso_now(),
                phase="design",
                intent="创建 plan scaffold",
                action="route:plan_only",
                key_output="password=secret",  # should be redacted
                decision_reason="因为 token=123 需要脱敏",
                result="success",
                risk="Bearer abcdef",
                highlights=("custom_reason: password=secret",),
            )
            session_dir = writer.append_event("run-1", event)
            writer.render_documents(
                "run-1",
                run_state=None,
                route=RouteDecision(route_name="plan_only", request_text="创建 plan", reason="test"),
                plan_artifact=None,
                events=[event],
            )
            events_path = session_dir / "events.jsonl"
            self.assertTrue(events_path.exists())
            self.assertIn("<REDACTED>", events_path.read_text(encoding="utf-8"))
            session_text = (session_dir / "session.md").read_text(encoding="utf-8")
            breakdown_text = (session_dir / "breakdown.md").read_text(encoding="utf-8")
            self.assertIn("<REDACTED>", session_text)
            self.assertIn("<REDACTED>", breakdown_text)

    def test_decision_replay_event_omits_raw_freeform_answers(self) -> None:
        rendered = build_strategy_pick_template(
            checkpoint_id="decision_replay_1",
            question="确认方案",
            summary="请选择本轮方向",
            options=(
                DecisionOption(option_id="option_1", title="方案一", summary="保守路径", recommended=True),
                DecisionOption(option_id="custom", title="自定义", summary="补充新方向"),
            ),
            language="zh-CN",
            recommended_option_id="option_1",
            default_option_id="option_1",
            allow_custom_option=True,
            constraint_field_type="input",
        )
        decision_state = DecisionState(
            schema_version="2",
            decision_id="decision_replay_1",
            feature_key="decision",
            phase="design",
            status="confirmed",
            decision_type="architecture_choice",
            question="确认方案",
            summary="请选择本轮方向",
            options=rendered.options,
            checkpoint=rendered.checkpoint,
            recommended_option_id=rendered.recommended_option_id,
            default_option_id=rendered.default_option_id,
            selection=DecisionSelection(
                option_id="custom",
                source="cli_text",
                raw_input="custom",
                answers={
                    PRIMARY_OPTION_FIELD_ID: "custom",
                    "custom_reason": "token=secret 需要走全新边界",
                    "implementation_constraint": "password=123 不能落日志",
                },
            ),
            updated_at=iso_now(),
        )

        event = build_decision_replay_event(
            decision_state,
            language="zh-CN",
            action="confirmed",
        )
        joined = "\n".join(event.highlights)

        self.assertIn("已提供补充说明", joined)
        self.assertNotIn("token=secret", joined)
        self.assertNotIn("password=123", joined)


class SkillRegistryTests(unittest.TestCase):
    def test_skill_registry_discovers_builtin_and_project_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            project_skill = workspace / "skills" / "local-demo"
            project_skill.mkdir(parents=True)
            (project_skill / "SKILL.md").write_text(
                "---\nname: local-demo\ndescription: local skill\n---\n\n# local\n",
                encoding="utf-8",
            )
            (project_skill / "skill.yaml").write_text(
                "id: local-demo\nmode: advisory\ntriggers:\n  - local\n",
                encoding="utf-8",
            )
            config = load_runtime_config(workspace)
            skills = SkillRegistry(config, user_home=workspace / "home").discover()
            skill_ids = {skill.skill_id for skill in skills}
            self.assertIn("analyze", skill_ids)
            self.assertIn("model-compare", skill_ids)
            self.assertIn("local-demo", skill_ids)
            model_compare = next(skill for skill in skills if skill.skill_id == "model-compare")
            self.assertEqual(model_compare.mode, "runtime")
            self.assertIsNotNone(model_compare.runtime_entry)
            self.assertEqual(model_compare.entry_kind, "python")
            self.assertEqual(model_compare.handoff_kind, "compare")
            self.assertEqual(model_compare.supports_routes, ("compare",))

    def test_skill_registry_builtin_catalog_does_not_require_builtin_skill_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            workspace = temp_root / "workspace"
            target_root = temp_root / "target"
            workspace.mkdir()
            target_root.mkdir()

            sync_script = REPO_ROOT / "scripts" / "sync-runtime-assets.sh"
            completed = subprocess.run(
                ["bash", str(sync_script), str(target_root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)

            bundle_root = target_root / ".sopify-runtime"
            config = load_runtime_config(workspace)
            skills = SkillRegistry(config, repo_root=bundle_root, user_home=workspace / "home").discover()
            skill_ids = {skill.skill_id for skill in skills}

            self.assertIn("analyze", skill_ids)
            self.assertIn("workflow-learning", skill_ids)
            self.assertIn("model-compare", skill_ids)

            model_compare = next(skill for skill in skills if skill.skill_id == "model-compare")
            self.assertEqual(model_compare.source, "builtin")
            self.assertEqual(model_compare.runtime_entry, (bundle_root / "scripts" / "model_compare_runtime.py").resolve())
            self.assertEqual(model_compare.path, (bundle_root / "runtime" / "builtin_catalog.py").resolve())

    def test_skill_registry_does_not_override_builtin_without_explicit_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            project_skill = workspace / "skills" / "analyze"
            project_skill.mkdir(parents=True)
            (project_skill / "SKILL.md").write_text(
                "---\nname: analyze\ndescription: local override attempt\n---\n\n# local\n",
                encoding="utf-8",
            )
            (project_skill / "skill.yaml").write_text(
                "id: analyze\nmode: advisory\n",
                encoding="utf-8",
            )

            config = load_runtime_config(workspace)
            skills = SkillRegistry(config, user_home=workspace / "home").discover()
            analyze = next(skill for skill in skills if skill.skill_id == "analyze")

            self.assertEqual(analyze.source, "builtin")
            self.assertNotEqual(analyze.description, "local override attempt")

    def test_skill_registry_allows_explicit_builtin_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            project_skill = workspace / "skills" / "analyze"
            project_skill.mkdir(parents=True)
            (project_skill / "SKILL.md").write_text(
                "---\nname: analyze\ndescription: local override\n---\n\n# local\n",
                encoding="utf-8",
            )
            (project_skill / "skill.yaml").write_text(
                "id: analyze\noverride_builtin: true\nmode: advisory\nsupports_routes:\n  - workflow\n",
                encoding="utf-8",
            )

            config = load_runtime_config(workspace)
            skills = SkillRegistry(config, user_home=workspace / "home").discover()
            analyze = next(skill for skill in skills if skill.skill_id == "analyze")

            self.assertEqual(analyze.source, "project")
            self.assertEqual(analyze.description, "local override")
            self.assertTrue(analyze.metadata.get("override_builtin"))
            self.assertEqual(analyze.supports_routes, ("workflow",))


class KnowledgeBaseBootstrapTests(unittest.TestCase):
    def test_progressive_bootstrap_creates_minimal_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)

            artifact = bootstrap_kb(config)

            self.assertEqual(
                set(artifact.files),
                {
                    ".sopify-skills/project.md",
                    ".sopify-skills/wiki/overview.md",
                    ".sopify-skills/user/preferences.md",
                    ".sopify-skills/history/index.md",
                },
            )
            self.assertIn("当前暂无已确认的长期偏好", (workspace / ".sopify-skills" / "user" / "preferences.md").read_text(encoding="utf-8"))
            self.assertIn("变更历史索引", (workspace / ".sopify-skills" / "history" / "index.md").read_text(encoding="utf-8"))
            self.assertTrue((workspace / ".sopify-skills" / "wiki" / "modules").is_dir())

    def test_full_bootstrap_creates_extended_kb_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "sopify.config.yaml").write_text("advanced:\n  kb_init: full\n", encoding="utf-8")
            config = load_runtime_config(workspace)

            artifact = bootstrap_kb(config)

            self.assertIn(".sopify-skills/wiki/arch.md", artifact.files)
            self.assertIn(".sopify-skills/wiki/api.md", artifact.files)
            self.assertIn(".sopify-skills/wiki/data.md", artifact.files)
            self.assertIn(".sopify-skills/user/feedback.jsonl", artifact.files)

    def test_bootstrap_is_idempotent_and_preserves_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)

            first = bootstrap_kb(config)
            self.assertTrue(first.files)

            project_path = workspace / ".sopify-skills" / "project.md"
            project_path.write_text("# custom\n", encoding="utf-8")

            second = bootstrap_kb(config)

            self.assertEqual(second.files, ())
            self.assertEqual(project_path.read_text(encoding="utf-8"), "# custom\n")

    def test_real_project_bootstrap_creates_blueprint_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "package.json").write_text('{"name":"sample-app"}', encoding="utf-8")
            config = load_runtime_config(workspace)

            artifact = bootstrap_kb(config)

            self.assertIn(".sopify-skills/blueprint/README.md", artifact.files)
            readme_path = workspace / ".sopify-skills" / "blueprint" / "README.md"
            self.assertTrue(readme_path.exists())
            self.assertIn("sopify:auto:goal:start", readme_path.read_text(encoding="utf-8"))


class EngineIntegrationTests(unittest.TestCase):
    def test_engine_enters_clarification_before_plan_materialization(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            result = run_runtime("~go plan 优化一下", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(result.route.route_name, "clarification_pending")
            self.assertIsNone(result.plan_artifact)
            self.assertIsNotNone(result.recovered_context.current_clarification)
            self.assertEqual(result.handoff.handoff_kind, "clarification")
            self.assertEqual(result.handoff.required_host_action, "answer_questions")
            self.assertIn("clarification_form", result.handoff.artifacts)
            self.assertEqual(result.handoff.artifacts["clarification_form"]["template_id"], "scope_clarify")
            self.assertEqual(result.handoff.artifacts["clarification_submission_state"]["status"], "empty")
            self.assertTrue((workspace / ".sopify-skills" / "state" / "current_clarification.json").exists())
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_plan.json").exists())

    def test_engine_resumes_planning_after_clarification_answer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run_runtime("~go plan 优化一下", workspace_root=workspace, user_home=workspace / "home")

            result = run_runtime(
                "目标是 runtime/router.py 和 runtime/engine.py，预期结果是接入 clarification_pending 状态骨架。",
                workspace_root=workspace,
                user_home=workspace / "home",
            )

            self.assertEqual(result.route.route_name, "plan_only")
            self.assertIsNotNone(result.plan_artifact)
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_clarification.json").exists())
            self.assertTrue((workspace / result.plan_artifact.path / "tasks.md").exists())

    def test_exec_plan_is_blocked_while_clarification_is_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run_runtime("~go plan 优化一下", workspace_root=workspace, user_home=workspace / "home")

            result = run_runtime("~go exec", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(result.route.route_name, "clarification_pending")
            self.assertIsNone(result.plan_artifact)
            self.assertEqual(result.handoff.required_host_action, "answer_questions")
            self.assertEqual(result.recovered_context.current_run.stage, "clarification_pending")

    def test_exec_plan_is_unavailable_without_active_recovery_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            result = run_runtime("~go exec", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(result.route.route_name, "exec_plan")
            self.assertIsNone(result.recovered_context.current_plan)
            self.assertIsNone(result.handoff)
            self.assertTrue(any("~go exec" in note for note in result.notes))
            rendered = render_runtime_output(
                result,
                brand="demo-ai",
                language="zh-CN",
                title_color="none",
                use_color=False,
            )
            self.assertIn("高级恢复入口", rendered)
            self.assertIn("Next: 仅在已有活动 plan 或恢复态时使用 ~go exec", rendered)

    def test_exec_plan_respects_execution_gate_before_develop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run_runtime(
                "~go plan payload 放 host root 还是 workspace/.sopify-runtime",
                workspace_root=workspace,
                user_home=workspace / "home",
            )
            run_runtime("1", workspace_root=workspace, user_home=workspace / "home")

            result = run_runtime("~go exec", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(result.route.route_name, "exec_plan")
            self.assertEqual(result.recovered_context.current_run.stage, "plan_generated")
            self.assertEqual(result.recovered_context.current_run.execution_gate.gate_status, "blocked")
            self.assertEqual(result.recovered_context.current_run.execution_gate.blocking_reason, "missing_info")
            self.assertIsNone(result.handoff)

    def test_ready_plan_enters_execution_confirm_flow_before_develop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            _prepare_ready_plan_state(workspace)

            result = run_runtime("~go exec", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(result.route.route_name, "execution_confirm_pending")
            self.assertEqual(result.recovered_context.current_run.stage, "execution_confirm_pending")
            self.assertEqual(result.handoff.required_host_action, "confirm_execute")
            summary = result.handoff.artifacts["execution_summary"]
            self.assertEqual(summary["plan_path"], result.recovered_context.current_plan.path)
            self.assertEqual(summary["task_count"], 5)
            self.assertIn("执行前确认", summary["key_risk"])
            self.assertIn("execution_confirm_pending", summary["mitigation"])
            rendered = render_runtime_output(
                result,
                brand="demo-ai",
                language="zh-CN",
                title_color="none",
                use_color=False,
            )
            self.assertIn("任务数: 5", rendered)
            self.assertIn("关键风险:", rendered)
            self.assertIn("Next: 回复 继续 / next / 开始 确认执行", rendered)

    def test_natural_language_execution_confirmation_starts_executing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            _prepare_ready_plan_state(workspace)
            run_runtime("~go exec", workspace_root=workspace, user_home=workspace / "home")

            result = run_runtime("开始", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(result.route.route_name, "resume_active")
            self.assertEqual(result.recovered_context.current_run.stage, "executing")
            self.assertEqual(result.handoff.required_host_action, "continue_host_develop")

    def test_execution_confirmation_feedback_routes_back_to_plan_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            _prepare_ready_plan_state(workspace)

            result = run_runtime("风险描述再具体一点", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(result.route.route_name, "execution_confirm_pending")
            self.assertEqual(result.recovered_context.current_run.stage, "execution_confirm_pending")
            self.assertEqual(result.handoff.required_host_action, "review_or_execute_plan")
            self.assertEqual(result.handoff.artifacts["execution_feedback"], "风险描述再具体一点")

    def test_engine_handles_plan_resume_and_cancel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            first = run_runtime("~go plan 补 runtime 骨架", workspace_root=workspace, user_home=workspace / "home")
            self.assertEqual(first.route.route_name, "plan_only")
            self.assertIsNotNone(first.plan_artifact)
            self.assertIsNotNone(first.replay_session_dir)
            self.assertTrue((workspace / ".sopify-skills" / "project.md").exists())
            self.assertTrue((workspace / ".sopify-skills" / "wiki" / "overview.md").exists())
            self.assertTrue((workspace / ".sopify-skills" / "user" / "preferences.md").exists())
            self.assertTrue((workspace / ".sopify-skills" / "history" / "index.md").exists())
            self.assertEqual(first.handoff.required_host_action, "review_or_execute_plan")
            self.assertTrue((workspace / ".sopify-skills" / "state" / "current_handoff.json").exists())

            resumed = run_runtime("继续", workspace_root=workspace, user_home=workspace / "home")
            self.assertEqual(resumed.route.route_name, "resume_active")
            self.assertTrue(resumed.recovered_context.has_active_run)
            self.assertTrue(resumed.recovered_context.loaded_files)
            self.assertIsNotNone(resumed.handoff)
            self.assertEqual(resumed.handoff.handoff_kind, "develop")
            self.assertEqual(resumed.handoff.required_host_action, "continue_host_develop")

            canceled = run_runtime("取消", workspace_root=workspace, user_home=workspace / "home")
            self.assertEqual(canceled.route.route_name, "cancel_active")
            store = StateStore(load_runtime_config(workspace))
            self.assertFalse(store.has_active_flow())
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_handoff.json").exists())

    def test_engine_populates_blueprint_scaffold_on_first_plan_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            result = run_runtime("~go plan 补 runtime 骨架", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(result.route.route_name, "plan_only")
            self.assertTrue((workspace / ".sopify-skills" / "blueprint" / "README.md").exists())
            self.assertTrue((workspace / ".sopify-skills" / "blueprint" / "background.md").exists())
            self.assertTrue((workspace / ".sopify-skills" / "blueprint" / "design.md").exists())
            self.assertTrue((workspace / ".sopify-skills" / "blueprint" / "tasks.md").exists())

    def test_engine_finalizes_metadata_managed_plan_into_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            first = run_runtime("~go plan 补 runtime 骨架", workspace_root=workspace, user_home=workspace / "home")
            self.assertIsNotNone(first.plan_artifact)

            result = run_runtime("~go finalize", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(result.route.route_name, "finalize_active")
            self.assertIsNotNone(result.plan_artifact)
            self.assertTrue(result.plan_artifact.path.startswith(".sopify-skills/history/"))
            self.assertFalse((workspace / first.plan_artifact.path).exists())
            self.assertTrue((workspace / result.plan_artifact.path).exists())
            self.assertTrue(any("review_required" in note for note in result.notes))
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_plan.json").exists())
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_run.json").exists())
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_handoff.json").exists())

            history_index = (workspace / ".sopify-skills" / "history" / "index.md").read_text(encoding="utf-8")
            self.assertIn(first.plan_artifact.plan_id, history_index)
            self.assertNotIn("当前暂无已归档方案。", history_index)

            blueprint_readme = (workspace / ".sopify-skills" / "blueprint" / "README.md").read_text(encoding="utf-8")
            self.assertIn("sopify:auto:focus:start", blueprint_readme)
            self.assertIn(result.plan_artifact.path, blueprint_readme)
            self.assertIn("当前已无活动 plan", blueprint_readme)

    def test_finalize_blocks_full_plan_without_deep_blueprint_update(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            first = run_runtime("实现 runtime plugin bridge", workspace_root=workspace, user_home=workspace / "home")
            self.assertIsNotNone(first.plan_artifact)
            self.assertEqual(first.plan_artifact.level, "full")

            result = run_runtime("~go finalize", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(result.route.route_name, "finalize_active")
            self.assertIsNone(result.plan_artifact)
            self.assertTrue(any("design_required" in note for note in result.notes))
            self.assertTrue((workspace / first.plan_artifact.path).exists())
            self.assertTrue((workspace / ".sopify-skills" / "state" / "current_plan.json").exists())

    def test_finalize_rejects_legacy_plan_without_front_matter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)
            store = StateStore(config)
            store.ensure()

            legacy_dir = workspace / ".sopify-skills" / "plan" / "legacy_plan"
            legacy_dir.mkdir(parents=True)
            legacy_tasks = legacy_dir / "tasks.md"
            legacy_tasks.write_text("# legacy plan\n", encoding="utf-8")

            store.set_current_plan(
                PlanArtifact(
                    plan_id="legacy_plan",
                    title="Legacy Plan",
                    summary="legacy",
                    level="standard",
                    path=".sopify-skills/plan/legacy_plan",
                    files=(".sopify-skills/plan/legacy_plan/tasks.md",),
                    created_at=iso_now(),
                )
            )
            store.set_current_run(
                RunState(
                    run_id="legacy-run",
                    status="active",
                    stage="plan_ready",
                    route_name="workflow",
                    title="Legacy Plan",
                    created_at=iso_now(),
                    updated_at=iso_now(),
                    plan_id="legacy_plan",
                    plan_path=".sopify-skills/plan/legacy_plan",
                )
            )

            result = run_runtime("~go finalize", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(result.route.route_name, "finalize_active")
            self.assertIsNone(result.plan_artifact)
            self.assertTrue(any("metadata-managed" in note for note in result.notes))
            self.assertTrue(legacy_tasks.exists())

    def test_engine_creates_decision_checkpoint_before_materializing_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            result = run_runtime(
                "~go plan payload 放 host root 还是 workspace/.sopify-runtime",
                workspace_root=workspace,
                user_home=workspace / "home",
            )

            self.assertEqual(result.route.route_name, "decision_pending")
            self.assertIsNone(result.plan_artifact)
            self.assertIsNotNone(result.recovered_context.current_decision)
            self.assertEqual(result.handoff.handoff_kind, "decision")
            self.assertEqual(result.handoff.required_host_action, "confirm_decision")
            self.assertTrue((workspace / ".sopify-skills" / "state" / "current_decision.json").exists())
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_plan.json").exists())
            self.assertTrue((workspace / ".sopify-skills" / "blueprint" / "design.md").exists())

    def test_engine_materializes_plan_after_decision_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run_runtime(
                "~go plan payload 放 host root 还是 workspace/.sopify-runtime",
                workspace_root=workspace,
                user_home=workspace / "home",
            )

            result = run_runtime("1", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(result.route.route_name, "plan_only")
            self.assertIsNotNone(result.plan_artifact)
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_decision.json").exists())
            self.assertEqual(result.recovered_context.current_run.stage, "plan_generated")
            self.assertEqual(result.recovered_context.current_run.execution_gate.gate_status, "blocked")
            self.assertEqual(result.handoff.artifacts["execution_gate"]["blocking_reason"], "missing_info")
            tasks_path = workspace / result.plan_artifact.path / "tasks.md"
            design_path = workspace / result.plan_artifact.path / "design.md"
            self.assertIn("decision_checkpoint:", tasks_path.read_text(encoding="utf-8"))
            self.assertIn("## 决策确认", design_path.read_text(encoding="utf-8"))

    def test_engine_accepts_explicit_option_id_command_for_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run_runtime(
                "~go plan payload 放 host root 还是 workspace/.sopify-runtime",
                workspace_root=workspace,
                user_home=workspace / "home",
            )

            result = run_runtime("~decide choose option_1", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(result.route.route_name, "plan_only")
            self.assertIsNotNone(result.plan_artifact)
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_decision.json").exists())

    def test_engine_materializes_plan_after_structured_decision_submission(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run_runtime(
                "~go plan payload 放 host root 还是 workspace/.sopify-runtime",
                workspace_root=workspace,
                user_home=workspace / "home",
            )

            store = StateStore(load_runtime_config(workspace))
            store.set_current_decision_submission(
                DecisionSubmission(
                    status="submitted",
                    source="cli",
                    answers={
                        "selected_option_id": "option_1",
                        "implementation_notes": "继续保持 manifest-first 与默认入口不变",
                    },
                    submitted_at=iso_now(),
                    resume_action="submit",
                )
            )

            result = run_runtime("继续", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(result.route.route_name, "plan_only")
            self.assertIsNotNone(result.plan_artifact)
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_decision.json").exists())
            self.assertEqual(result.recovered_context.current_run.stage, "plan_generated")
            self.assertTrue(any("structured submission" in note for note in result.notes))

    def test_confirmed_decision_can_resume_after_interruption(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            pending = run_runtime(
                "~go plan payload 放 host root 还是 workspace/.sopify-runtime",
                workspace_root=workspace,
                user_home=workspace / "home",
            )

            config = load_runtime_config(workspace)
            store = StateStore(config)
            confirmed = confirm_decision(
                pending.recovered_context.current_decision,
                option_id="option_1",
                source="text",
                raw_input="1",
            )
            store.set_current_decision(confirmed)

            resumed = run_runtime("继续", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(resumed.route.route_name, "plan_only")
            self.assertIsNotNone(resumed.plan_artifact)
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_decision.json").exists())

    def test_confirmed_decision_can_materialize_through_exec_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            pending = run_runtime(
                "~go plan payload 放 host root 还是 workspace/.sopify-runtime",
                workspace_root=workspace,
                user_home=workspace / "home",
            )

            config = load_runtime_config(workspace)
            store = StateStore(config)
            confirmed = confirm_decision(
                pending.recovered_context.current_decision,
                option_id="option_1",
                source="text",
                raw_input="1",
            )
            store.set_current_decision(confirmed)

            resumed = run_runtime("~go exec", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(resumed.route.route_name, "plan_only")
            self.assertIsNotNone(resumed.plan_artifact)
            self.assertEqual(resumed.recovered_context.current_run.stage, "plan_generated")
            self.assertEqual(resumed.recovered_context.current_run.execution_gate.blocking_reason, "missing_info")
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_decision.json").exists())

    def test_confirmed_gate_decision_reenters_execution_gate_on_existing_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)
            store = StateStore(config)
            store.ensure()
            plan_artifact = create_plan_scaffold("调整 auth boundary", config=config, level="standard")
            _rewrite_background_scope(
                workspace,
                plan_artifact,
                scope_lines=("runtime/engine.py", "runtime/engine.py, runtime/router.py"),
                risk_lines=("本轮会调整认证与权限边界", "需要先明确批准路径"),
            )
            route = RouteDecision(
                route_name="workflow",
                request_text="调整 auth boundary",
                reason="test",
                complexity="complex",
                plan_level="standard",
                candidate_skill_ids=("design", "develop"),
            )
            gate = evaluate_execution_gate(
                decision=route,
                plan_artifact=plan_artifact,
                current_clarification=None,
                current_decision=None,
                config=config,
            )
            gate_decision = build_execution_gate_decision_state(
                route,
                gate=gate,
                current_plan=plan_artifact,
                config=config,
            )
            self.assertIsNotNone(gate_decision)
            store.set_current_plan(plan_artifact)
            store.set_current_run(
                RunState(
                    run_id="run-1",
                    status="active",
                    stage="decision_pending",
                    route_name="workflow",
                    title=plan_artifact.title,
                    created_at=iso_now(),
                    updated_at=iso_now(),
                    plan_id=plan_artifact.plan_id,
                    plan_path=plan_artifact.path,
                    execution_gate=gate,
                )
            )
            confirmed = confirm_decision(
                gate_decision,
                option_id="option_1",
                source="text",
                raw_input="1",
            )
            store.set_current_decision(confirmed)

            resumed = run_runtime("继续", workspace_root=workspace, user_home=workspace / "home")

            self.assertEqual(resumed.route.route_name, "execution_confirm_pending")
            self.assertIsNotNone(resumed.plan_artifact)
            self.assertEqual(resumed.plan_artifact.path, plan_artifact.path)
            self.assertEqual(resumed.recovered_context.current_run.stage, "ready_for_execution")
            self.assertEqual(resumed.recovered_context.current_run.execution_gate.gate_status, "ready")
            self.assertEqual(resumed.handoff.required_host_action, "confirm_execute")
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_decision.json").exists())

    def test_engine_handoff_contracts_cover_compare_and_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            compare = run_runtime("~compare 方案对比", workspace_root=workspace, user_home=workspace / "home")
            self.assertIsNotNone(compare.handoff)
            self.assertEqual(compare.handoff.handoff_kind, "compare")
            self.assertEqual(compare.handoff.required_host_action, "host_compare_bridge_required")

            replay = run_runtime("回放最近一次实现", workspace_root=workspace, user_home=workspace / "home")
            self.assertIsNotNone(replay.handoff)
            self.assertEqual(replay.handoff.handoff_kind, "replay")
            self.assertEqual(replay.handoff.required_host_action, "host_replay_bridge_required")

    def test_compare_handoff_attaches_decision_facade_when_runtime_returns_results(self) -> None:
        def model_caller(candidate, payload, timeout_sec):
            return {"answer": f"{candidate.id} suggests using an adapter boundary for {payload['question']}"}

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            compare = run_runtime(
                "~compare adapter boundary vs direct host coupling",
                workspace_root=workspace,
                user_home=workspace / "home",
                runtime_payloads={
                    "model-compare": {
                        "question": "adapter boundary vs direct host coupling",
                        "multi_model_config": {
                            "enabled": True,
                            "include_default_model": True,
                            "context_bridge": False,
                            "candidates": [
                                {
                                    "id": "external_a",
                                    "provider": "openai_compatible",
                                    "model": "demo-a",
                                    "enabled": True,
                                    "api_key_env": "TEST_COMPARE_KEY",
                                }
                            ],
                        },
                        "model_caller": model_caller,
                        "default_candidate": make_default_candidate(),
                        "env": {"TEST_COMPARE_KEY": "sk-demo"},
                    }
                },
            )

            self.assertIsNotNone(compare.handoff)
            self.assertEqual(compare.handoff.required_host_action, "review_compare_results")
            contract = compare.handoff.artifacts.get("compare_decision_contract")
            self.assertIsInstance(contract, dict)
            self.assertEqual(contract["decision_type"], "compare_result_choice")
            self.assertIn("checkpoint", contract)
            self.assertEqual(contract["recommended_option_id"], "session_default")

    def test_rendered_plan_output_and_repo_local_helper(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            result = run_runtime("~go plan 补 runtime 骨架", workspace_root=workspace, user_home=workspace / "home")
            rendered = render_runtime_output(
                result,
                brand="demo-ai",
                language="zh-CN",
                title_color="none",
                use_color=False,
            )

            self.assertIn("[demo-ai] 方案设计 ✓", rendered)
            self.assertIn("方案: .sopify-skills/plan/", rendered)
            self.assertIn("交接: .sopify-skills/state/current_handoff.json", rendered)
            self.assertIn("Next: 在宿主会话中继续评审或执行方案，或直接回复修改意见", rendered)

            script_path = REPO_ROOT / "scripts" / "go_plan_runtime.py"
            completed = subprocess.run(
                [sys.executable, str(script_path), "--workspace-root", str(workspace), "--no-color", "补 runtime 骨架"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("[tmp", completed.stdout)
            self.assertTrue((workspace / ".sopify-skills" / "state" / "current_plan.json").exists())
            self.assertTrue((workspace / ".sopify-skills" / "replay" / "sessions").exists())
            self.assertTrue((workspace / ".sopify-skills" / "project.md").exists())
            self.assertIn(".sopify-skills/project.md", rendered)

    def test_go_plan_helper_allows_pending_decision_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            script_path = REPO_ROOT / "scripts" / "go_plan_runtime.py"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--workspace-root",
                    str(workspace),
                    "--no-color",
                    "payload",
                    "放",
                    "host",
                    "root",
                    "还是",
                    "workspace/.sopify-runtime",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("方案设计 ?", completed.stdout)
            self.assertTrue((workspace / ".sopify-skills" / "state" / "current_decision.json").exists())

    def test_go_plan_helper_allows_pending_clarification_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            script_path = REPO_ROOT / "scripts" / "go_plan_runtime.py"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--workspace-root",
                    str(workspace),
                    "--no-color",
                    "优化一下",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("需求分析 ?", completed.stdout)
            self.assertTrue((workspace / ".sopify-skills" / "state" / "current_clarification.json").exists())

    def test_synced_runtime_bundle_runs_in_another_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target_root = temp_root / "target"
            workspace = temp_root / "workspace"
            target_root.mkdir()
            workspace.mkdir()

            sync_script = REPO_ROOT / "scripts" / "sync-runtime-assets.sh"
            sync_completed = subprocess.run(
                ["bash", str(sync_script), str(target_root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(sync_completed.returncode, 0, msg=sync_completed.stderr)

            bundle_root = target_root / ".sopify-runtime"
            manifest_path = bundle_root / "manifest.json"
            self.assertTrue((bundle_root / "runtime" / "__init__.py").exists())
            self.assertTrue((bundle_root / "runtime" / "clarification_bridge.py").exists())
            self.assertTrue((bundle_root / "runtime" / "cli_interactive.py").exists())
            self.assertTrue((bundle_root / "runtime" / "execution_confirm.py").exists())
            self.assertTrue((bundle_root / "runtime" / "decision_bridge.py").exists())
            self.assertTrue((bundle_root / "scripts" / "check-runtime-smoke.sh").exists())
            self.assertTrue((bundle_root / "scripts" / "clarification_bridge_runtime.py").exists())
            self.assertTrue((bundle_root / "scripts" / "decision_bridge_runtime.py").exists())
            self.assertTrue((bundle_root / "tests" / "test_runtime.py").exists())
            self.assertTrue(manifest_path.exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], "1")
            self.assertEqual(manifest["default_entry"], "scripts/sopify_runtime.py")
            self.assertEqual(manifest["plan_only_entry"], "scripts/go_plan_runtime.py")
            self.assertEqual(manifest["handoff_file"], ".sopify-skills/state/current_handoff.json")
            self.assertEqual(manifest["capabilities"]["bundle_role"], "control_plane")
            self.assertTrue(manifest["capabilities"]["writes_handoff_file"])
            self.assertTrue(manifest["capabilities"]["clarification_checkpoint"])
            self.assertTrue(manifest["capabilities"]["clarification_bridge"])
            self.assertTrue(manifest["capabilities"]["writes_clarification_file"])
            self.assertTrue(manifest["capabilities"]["decision_checkpoint"])
            self.assertTrue(manifest["capabilities"]["decision_bridge"])
            self.assertTrue(manifest["capabilities"]["execution_gate"])
            self.assertTrue(manifest["capabilities"]["writes_decision_file"])
            self.assertIn("plan_only", manifest["limits"]["host_required_routes"])
            self.assertIn("clarification_pending", manifest["limits"]["host_required_routes"])
            self.assertIn("clarification_resume", manifest["limits"]["host_required_routes"])
            self.assertIn("execution_confirm_pending", manifest["limits"]["host_required_routes"])
            self.assertIn("decision_pending", manifest["limits"]["host_required_routes"])
            self.assertIn("finalize_active", manifest["supported_routes"])
            self.assertIn("compare", manifest["supported_routes"])
            self.assertIn("exec_plan", manifest["limits"]["host_required_routes"])
            self.assertEqual(manifest["limits"]["clarification_file"], ".sopify-skills/state/current_clarification.json")
            self.assertEqual(manifest["limits"]["clarification_bridge_entry"], "scripts/clarification_bridge_runtime.py")
            self.assertEqual(manifest["limits"]["clarification_bridge_hosts"]["cli"]["preferred_mode"], "interactive_form")
            self.assertEqual(manifest["limits"]["decision_file"], ".sopify-skills/state/current_decision.json")
            self.assertEqual(manifest["limits"]["decision_bridge_entry"], "scripts/decision_bridge_runtime.py")
            self.assertEqual(manifest["limits"]["decision_bridge_hosts"]["cli"]["preferred_mode"], "interactive_form")
            self.assertEqual(manifest["limits"]["decision_bridge_hosts"]["cli"]["select"], "interactive_select")
            self.assertIn("model-compare", manifest["limits"]["runtime_payload_required_skill_ids"])
            self.assertEqual(len(manifest["builtin_skills"]), 7)
            model_compare = next(skill for skill in manifest["builtin_skills"] if skill["skill_id"] == "model-compare")
            self.assertEqual(model_compare["runtime_entry"], "scripts/model_compare_runtime.py")
            self.assertEqual(model_compare["entry_kind"], "python")
            self.assertEqual(model_compare["supports_routes"], ["compare"])

            runtime_script = bundle_root / "scripts" / "sopify_runtime.py"
            completed = subprocess.run(
                [sys.executable, str(runtime_script), "--workspace-root", str(workspace), "--no-color", "重构数据库层"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn(".sopify-skills/plan/", completed.stdout)
            self.assertTrue((workspace / ".sopify-skills" / "state" / "current_handoff.json").exists())
            self.assertTrue((workspace / ".sopify-skills" / "state" / "current_plan.json").exists())
            self.assertTrue((workspace / ".sopify-skills" / "replay" / "sessions").exists())
            self.assertTrue((workspace / ".sopify-skills" / "project.md").exists())
            self.assertTrue((workspace / ".sopify-skills" / "history" / "index.md").exists())

    def test_synced_runtime_bundle_supports_decision_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target_root = temp_root / "target"
            workspace = temp_root / "workspace"
            target_root.mkdir()
            workspace.mkdir()

            sync_script = REPO_ROOT / "scripts" / "sync-runtime-assets.sh"
            sync_completed = subprocess.run(
                ["bash", str(sync_script), str(target_root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(sync_completed.returncode, 0, msg=sync_completed.stderr)

            runtime_script = target_root / ".sopify-runtime" / "scripts" / "sopify_runtime.py"
            bridge_script = target_root / ".sopify-runtime" / "scripts" / "decision_bridge_runtime.py"
            pending = subprocess.run(
                [
                    sys.executable,
                    str(runtime_script),
                    "--workspace-root",
                    str(workspace),
                    "--no-color",
                    "~go",
                    "plan",
                    "payload",
                    "放",
                    "host",
                    "root",
                    "还是",
                    "workspace/.sopify-runtime",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(pending.returncode, 0, msg=pending.stderr)
            self.assertIn("方案设计 ?", pending.stdout)
            self.assertTrue((workspace / ".sopify-skills" / "state" / "current_decision.json").exists())

            inspected = subprocess.run(
                [
                    sys.executable,
                    str(bridge_script),
                    "--workspace-root",
                    str(workspace),
                    "inspect",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(inspected.returncode, 0, msg=inspected.stderr)
            inspect_payload = json.loads(inspected.stdout)
            self.assertEqual(inspect_payload["bridge"]["host_kind"], "cli")
            self.assertEqual(inspect_payload["bridge"]["steps"][0]["renderer"], "cli.select")

            confirmed = subprocess.run(
                [
                    sys.executable,
                    str(bridge_script),
                    "--workspace-root",
                    str(workspace),
                    "submit",
                    "--answers-json",
                    '{"selected_option_id":"option_1"}',
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(confirmed.returncode, 0, msg=confirmed.stderr)
            confirmed_payload = json.loads(confirmed.stdout)
            self.assertEqual(confirmed_payload["status"], "written")

            resumed = subprocess.run(
                [
                    sys.executable,
                    str(runtime_script),
                    "--workspace-root",
                    str(workspace),
                    "--no-color",
                    "继续",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(resumed.returncode, 0, msg=resumed.stderr)
            self.assertIn(".sopify-skills/plan/", resumed.stdout)
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_decision.json").exists())
            self.assertTrue((workspace / ".sopify-skills" / "state" / "current_plan.json").exists())

    def test_synced_runtime_bundle_supports_cli_decision_bridge_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target_root = temp_root / "target"
            workspace = temp_root / "workspace"
            target_root.mkdir()
            workspace.mkdir()

            sync_script = REPO_ROOT / "scripts" / "sync-runtime-assets.sh"
            sync_completed = subprocess.run(
                ["bash", str(sync_script), str(target_root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(sync_completed.returncode, 0, msg=sync_completed.stderr)

            runtime_script = target_root / ".sopify-runtime" / "scripts" / "sopify_runtime.py"
            bridge_script = target_root / ".sopify-runtime" / "scripts" / "decision_bridge_runtime.py"
            pending = subprocess.run(
                [
                    sys.executable,
                    str(runtime_script),
                    "--workspace-root",
                    str(workspace),
                    "--no-color",
                    "~go",
                    "plan",
                    "payload",
                    "放",
                    "host",
                    "root",
                    "还是",
                    "workspace/.sopify-runtime",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(pending.returncode, 0, msg=pending.stderr)
            self.assertTrue((workspace / ".sopify-skills" / "state" / "current_decision.json").exists())

            prompted = subprocess.run(
                [
                    sys.executable,
                    str(bridge_script),
                    "--workspace-root",
                    str(workspace),
                    "prompt",
                    "--renderer",
                    "text",
                ],
                input="1\n",
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(prompted.returncode, 0, msg=prompted.stderr)
            prompted_payload = json.loads(prompted.stdout)
            self.assertEqual(prompted_payload["status"], "written")
            self.assertEqual(prompted_payload["used_renderer"], "text")
            self.assertEqual(prompted_payload["submission"]["answers"]["selected_option_id"], "option_1")

            resumed = subprocess.run(
                [
                    sys.executable,
                    str(runtime_script),
                    "--workspace-root",
                    str(workspace),
                    "--no-color",
                    "继续",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(resumed.returncode, 0, msg=resumed.stderr)
            self.assertIn(".sopify-skills/plan/", resumed.stdout)
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_decision.json").exists())

    def test_synced_runtime_bundle_supports_clarification_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            target_root = temp_root / "target"
            workspace = temp_root / "workspace"
            target_root.mkdir()
            workspace.mkdir()

            sync_script = REPO_ROOT / "scripts" / "sync-runtime-assets.sh"
            sync_completed = subprocess.run(
                ["bash", str(sync_script), str(target_root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(sync_completed.returncode, 0, msg=sync_completed.stderr)

            runtime_script = target_root / ".sopify-runtime" / "scripts" / "sopify_runtime.py"
            pending = subprocess.run(
                [
                    sys.executable,
                    str(runtime_script),
                    "--workspace-root",
                    str(workspace),
                    "--no-color",
                    "~go",
                    "plan",
                    "优化一下",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(pending.returncode, 0, msg=pending.stderr)
            self.assertIn("需求分析 ?", pending.stdout)
            self.assertTrue((workspace / ".sopify-skills" / "state" / "current_clarification.json").exists())

            answered = subprocess.run(
                [
                    sys.executable,
                    str(runtime_script),
                    "--workspace-root",
                    str(workspace),
                    "--no-color",
                    "目标是 runtime/router.py，预期结果是补 clarification_pending 状态骨架",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(answered.returncode, 0, msg=answered.stderr)
            self.assertIn(".sopify-skills/plan/", answered.stdout)
            self.assertFalse((workspace / ".sopify-skills" / "state" / "current_clarification.json").exists())
            self.assertTrue((workspace / ".sopify-skills" / "state" / "current_plan.json").exists())


if __name__ == "__main__":
    unittest.main()
