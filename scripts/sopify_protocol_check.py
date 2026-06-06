#!/usr/bin/env python3
"""sopify_protocol_check — P8 protocol kernel compliance checker.

Checks that a workspace conforms to the P8 post-cutover Sopify protocol:
- active_plan.json + current_handoff.json (2-file state model)
- plan.md with 8 required sections in order
- receipts/ with correct naming
- No forbidden patterns in active contract surfaces

Usage:
    python3 scripts/sopify_protocol_check.py check --scenario <new-plan|continuation|finalize> --fixture <path>

Output: JSON to stdout {scenario, verdict, failures, evidence}
"""

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "Context / Why",
    "Scope",
    "Approach",
    "Waves / Steps",
    "Key Decisions",
    "Constraints / Not-in-scope",
    "Status / Progress",
    "Next",
]

# Patterns that must NOT appear in active contract surfaces.
# Matches in [RETIRED], [DEPRECATED], [SUPERSEDED], MUST NOT, 禁止, ~~ contexts are allowed.
FORBIDDEN_PATTERNS = [
    (r"runtime_gate\.py\s+enter", "runtime_gate.py enter (active invocation)"),
    (r"gate_passed\s*==\s*true", "gate pass condition"),
    (r"strict_runtime_entry", "strict runtime entry"),
    (r"allowed_response_mode", "allowed_response_mode (gate contract)"),
]

FORBIDDEN_STATE_FILES = [
    "current_run.json",
    "current_plan.json",
    "current_clarification.json",
    "current_decision.json",
    "current_gate_receipt.json",
    "current_archive_receipt.json",
]

ALLOWANCE_MARKERS = [
    "[retired", "[deprecated", "[superseded",
    "must not", "must_not",
    "禁止", "不得", "退场",
    "~~", "pre-p8", "legacy",
]


def is_allowance_line(line: str) -> bool:
    low = line.lower()
    return any(m in low for m in ALLOWANCE_MARKERS)


def extract_h2_headings(plan_md: Path) -> list[str]:
    headings = []
    try:
        for line in plan_md.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("## ") and not stripped.startswith("### "):
                headings.append(stripped[3:].strip())
    except FileNotFoundError:
        pass
    return headings


def check_required_sections(plan_md: Path) -> list[str]:
    failures = []
    headings = extract_h2_headings(plan_md)
    found = []
    for h in headings:
        if h in REQUIRED_SECTIONS:
            found.append(h)
    for i, sec in enumerate(REQUIRED_SECTIONS):
        if sec not in found:
            failures.append(f"Missing required section: '{sec}'")
        elif i > 0 and found.index(sec) < found.index(REQUIRED_SECTIONS[i - 1]) if REQUIRED_SECTIONS[i - 1] in found else False:
            failures.append(f"Section '{sec}' out of order (must come after '{REQUIRED_SECTIONS[i - 1]}')")
    return failures


def check_forbidden_patterns(target_file: Path) -> list[str]:
    failures = []
    try:
        for line_num, line in enumerate(target_file.read_text(encoding="utf-8").splitlines(), 1):
            if is_allowance_line(line):
                continue
            for pattern, desc in FORBIDDEN_PATTERNS:
                if re.search(pattern, line):
                    failures.append(f"{target_file.name}:{line_num}: active reference to {desc}")
            for sf in FORBIDDEN_STATE_FILES:
                # Only flag if it looks like an active read reference, not a retirement note
                if sf in line and not any(kw in line for kw in [
                    "删除", "P8 删除", "RETIRED", "折叠", "替代", "退场", "legacy"
                ]):
                    failures.append(f"{target_file.name}:{line_num}: active reference to retired state file '{sf}'")
    except FileNotFoundError:
        pass
    return failures


def check_active_plan(state_dir: Path, expected_plan_id: str | None = None) -> tuple[dict | None, list[str]]:
    failures = []
    ap_file = state_dir / "active_plan.json"
    if not ap_file.exists():
        failures.append("Missing state/active_plan.json")
        return None, failures
    try:
        data = json.loads(ap_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            failures.append("active_plan.json is not a JSON object")
            return None, failures
    except json.JSONDecodeError as e:
        failures.append(f"Invalid JSON in active_plan.json: {e}")
        return None, failures
    if "plan_id" not in data:
        failures.append("active_plan.json missing required field 'plan_id'")
    if not isinstance(data.get("plan_id"), str) or not data["plan_id"]:
        failures.append("active_plan.json 'plan_id' must be a non-empty string")
    if expected_plan_id and data.get("plan_id") != expected_plan_id:
        failures.append(f"active_plan.json plan_id '{data.get('plan_id')}' != expected '{expected_plan_id}'")
    extra = set(data.keys()) - {"plan_id"}
    if extra:
        failures.append(f"active_plan.json has unexpected fields: {extra}")
    return data, failures


def check_current_handoff(state_dir: Path, expected_plan_id: str | None = None) -> tuple[dict | None, list[str]]:
    failures = []
    ch_file = state_dir / "current_handoff.json"
    if not ch_file.exists():
        failures.append("Missing state/current_handoff.json")
        return None, failures
    try:
        data = json.loads(ch_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            failures.append("current_handoff.json is not a JSON object")
            return None, failures
    except json.JSONDecodeError as e:
        failures.append(f"Invalid JSON in current_handoff.json: {e}")
        return None, failures
    for field in ["schema_version", "plan_id", "required_host_action"]:
        if field not in data:
            failures.append(f"current_handoff.json missing required field '{field}'")
    valid_actions = [
        "continue_host_develop", "answer_questions", "confirm_decision",
        "continue_host_consult", "resolve_state_conflict",
    ]
    action = data.get("required_host_action")
    if action and action not in valid_actions:
        failures.append(f"current_handoff.json invalid required_host_action: '{action}'")
    retired = ["route_name", "run_id", "handoff_kind", "resolution_id"]
    for f in retired:
        if f in data:
            failures.append(f"current_handoff.json has retired field '{f}' (move to observability.provenance)")
    if expected_plan_id and data.get("plan_id") != expected_plan_id:
        failures.append(f"current_handoff.json plan_id mismatch: '{data.get('plan_id')}' != '{expected_plan_id}'")
    return data, failures


def check_receipts(plan_dir: Path, require_final: bool = False) -> list[str]:
    failures = []
    receipts_dir = plan_dir / "receipts"
    if require_final:
        if not receipts_dir.exists():
            failures.append("Missing receipts/ directory (required for finalize)")
            return failures
        final = receipts_dir / "final.json"
        if not final.exists():
            failures.append("Missing receipts/final.json (required for finalize)")
        else:
            try:
                data = json.loads(final.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    failures.append("receipts/final.json is not a JSON object")
                    return failures
                for field in ["verdict", "evidence", "provenance", "timestamp"]:
                    if field not in data:
                        failures.append(f"receipts/final.json missing required field '{field}'")
            except json.JSONDecodeError as e:
                failures.append(f"Invalid JSON in receipts/final.json: {e}")
    elif receipts_dir.exists():
        for f in receipts_dir.iterdir():
            if f.name == "final.json":
                continue
            if not re.match(r"^(exec|verify)_\d{3}\.json$", f.name):
                failures.append(f"receipts/{f.name} doesn't match naming convention (exec_NNN/verify_NNN.json)")
    return failures


def check_state_empty(state_dir: Path) -> list[str]:
    failures = []
    if state_dir.exists():
        for f in state_dir.iterdir():
            if f.name in ("active_plan.json", "current_handoff.json"):
                continue
            failures.append(f"state/ should be empty after finalize, but found: {f.name}")
    return failures


def check_history_receipt(history_dir: Path) -> list[str]:
    failures = []
    receipt = history_dir / "receipt.md"
    if not receipt.exists():
        failures.append("Missing history receipt.md")
        return failures
    content = receipt.read_text(encoding="utf-8").lower()
    for keyword in ["outcome", "summary", "key_decisions"]:
        if keyword.replace("_", " ") not in content and keyword not in content:
            failures.append(f"history receipt.md missing section: '{keyword}'")
    return failures


def run_new_plan(fixture: Path) -> dict:
    failures = []
    sopify = fixture / ".sopify-skills"
    state = sopify / "state"
    plan_root = sopify / "plan"

    ap_data, ap_failures = check_active_plan(state)
    failures.extend(ap_failures)

    if ap_data:
        plan_id = ap_data.get("plan_id", "")
        plan_dir = plan_root / plan_id
        plan_md = plan_dir / "plan.md"
        if not plan_md.exists():
            failures.append(f"plan/{plan_id}/plan.md not found")
        else:
            failures.extend(check_required_sections(plan_md))
            failures.extend(check_forbidden_patterns(plan_md))

    return make_result("new-plan", failures, fixture)


def run_continuation(fixture: Path) -> dict:
    failures = []
    sopify = fixture / ".sopify-skills"
    state = sopify / "state"
    plan_root = sopify / "plan"
    protocol_md = sopify / "blueprint" / "protocol.md"

    # Step 1: active_plan
    ap_data, ap_failures = check_active_plan(state)
    failures.extend(ap_failures)
    plan_id = ap_data.get("plan_id", "") if ap_data else ""

    # Step 2: plan.md
    if plan_id:
        plan_dir = plan_root / plan_id
        plan_md = plan_dir / "plan.md"
        if not plan_md.exists():
            failures.append(f"plan/{plan_id}/plan.md not found (state inconsistency)")
        else:
            failures.extend(check_required_sections(plan_md))
            failures.extend(check_forbidden_patterns(plan_md))

    # Step 3: current_handoff
    ch_data, ch_failures = check_current_handoff(state, expected_plan_id=plan_id or None)
    failures.extend(ch_failures)

    # Step 4: receipts (latest-only)
    if plan_id:
        plan_dir = plan_root / plan_id
        failures.extend(check_receipts(plan_dir, require_final=False))

    # Protocol entry check: scan protocol.md for forbidden patterns
    if protocol_md.exists():
        failures.extend(check_forbidden_patterns(protocol_md))
    else:
        # Fallback: scan the repo's own protocol.md if fixture doesn't have one
        repo_protocol = Path(__file__).resolve().parent.parent / ".sopify-skills" / "blueprint" / "protocol.md"
        if repo_protocol.exists():
            failures.extend(check_forbidden_patterns(repo_protocol))
        # Also scan host prompt entry spec
        repo_prompt_spec = Path(__file__).resolve().parent.parent / ".sopify-skills" / "plan" / "20260605_p8_protocol_kernel_runtime_retirement" / "assets" / "host-prompt-protocol-entry.md"
        if repo_prompt_spec.exists():
            failures.extend(check_forbidden_patterns(repo_prompt_spec))

    # Check _registry.yaml not in entry path
    registry = sopify / "plan" / "_registry.yaml"
    if registry.exists():
        failures.append("_registry.yaml found in plan/ (must be deleted in P8)")

    return make_result("continuation", failures, fixture)


def run_finalize(fixture: Path) -> dict:
    failures = []
    sopify = fixture / ".sopify-skills"
    state = sopify / "state"
    history_root = sopify / "history"

    # State should be empty after finalize
    failures.extend(check_state_empty(state))

    # Check history has a receipt
    if history_root.exists():
        for month_dir in history_root.iterdir():
            if month_dir.is_dir():
                for plan_dir in month_dir.iterdir():
                    if plan_dir.is_dir():
                        failures.extend(check_history_receipt(plan_dir))
                        failures.extend(check_receipts(plan_dir, require_final=True))

    return make_result("finalize", failures, fixture)


def make_result(scenario: str, failures: list[str], fixture: Path) -> dict:
    return {
        "scenario": scenario,
        "verdict": "PASS" if not failures else "FAIL",
        "failures": failures,
        "evidence": {"fixture": str(fixture)},
    }


def main():
    parser = argparse.ArgumentParser(description="Sopify P8 protocol check")
    sub = parser.add_subparsers(dest="command")
    check_p = sub.add_parser("check")
    check_p.add_argument("--scenario", required=True, choices=["new-plan", "continuation", "finalize"])
    check_p.add_argument("--fixture", required=True, type=Path)
    args = parser.parse_args()

    if args.command != "check":
        parser.print_help()
        sys.exit(1)

    if not args.fixture.exists():
        print(json.dumps({"error": f"fixture not found: {args.fixture}"}), file=sys.stderr)
        sys.exit(2)

    runners = {
        "new-plan": run_new_plan,
        "continuation": run_continuation,
        "finalize": run_finalize,
    }
    try:
        result = runners[args.scenario](args.fixture)
    except Exception as e:
        result = {
            "scenario": args.scenario,
            "verdict": "FAIL",
            "failures": [f"Unexpected error: {type(e).__name__}: {e}"],
            "evidence": {"fixture": str(args.fixture)},
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
