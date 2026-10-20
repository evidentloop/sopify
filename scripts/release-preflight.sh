#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: scripts/release-preflight.sh

Run release preflight checks before bumping Sopify version:
  1) Verify version consistency and golden snapshots
  2) Check builtin catalog drift and run the full test suite
  3) Run protocol + payload smoke checks
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

run_step() {
  local title="$1"
  shift
  echo "[release-preflight] $title"
  "$@"
}

check_builtin_catalog_drift() {
  local tmp
  tmp="$(mktemp)"
  python3 "$ROOT_DIR/scripts/generate-builtin-catalog.py" --output "$tmp" >/dev/null
  if ! python3 - "$ROOT_DIR/skills/catalog/builtin_catalog.generated.json" "$tmp" <<'PY'; then
import difflib
import json
from pathlib import Path
import sys


def normalize(path_str: str) -> list[str]:
    payload = json.loads(Path(path_str).read_text(encoding="utf-8"))
    payload.pop("generated_at", None)
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).splitlines()


left_path, right_path = sys.argv[1], sys.argv[2]
left = normalize(left_path)
right = normalize(right_path)
if left != right:
    for line in difflib.unified_diff(left, right, fromfile=left_path, tofile=right_path, lineterm=""):
        print(line)
    raise SystemExit(1)
PY
    rm -f "$tmp"
    return 1
  fi
  rm -f "$tmp"
}

run_step "Check version consistency" bash "$ROOT_DIR/scripts/check-version-consistency.sh"

# A check must not accept changed snapshots or modify the caller's index.
# Intentional version updates still regenerate snapshots in release-sync.sh.
run_step "Check golden snapshots" python3 -m pytest "$ROOT_DIR/tests/test_golden_snapshots.py" -q
run_step "Check builtin catalog drift" check_builtin_catalog_drift
run_step "Run full test suite" python3 -m pytest "$ROOT_DIR/tests/" -q
run_step "Run protocol smoke — new-plan" python3 "$ROOT_DIR/scripts/sopify_protocol_check.py" check --scenario new-plan --fixture "$ROOT_DIR/tests/fixtures/minimal_plan"
run_step "Run protocol smoke — continuation" python3 "$ROOT_DIR/scripts/sopify_protocol_check.py" check --scenario continuation --fixture "$ROOT_DIR/tests/fixtures/minimal_plan"
run_step "Run protocol smoke — continuation (clarification pending)" python3 "$ROOT_DIR/scripts/sopify_protocol_check.py" check --scenario continuation --fixture "$ROOT_DIR/tests/fixtures/clarification_pending"
run_step "Run protocol smoke — continuation (decision pending)" python3 "$ROOT_DIR/scripts/sopify_protocol_check.py" check --scenario continuation --fixture "$ROOT_DIR/tests/fixtures/decision_pending"
run_step "Run protocol smoke — finalize" python3 "$ROOT_DIR/scripts/sopify_protocol_check.py" check --scenario finalize --fixture "$ROOT_DIR/tests/fixtures/finalized_plan"
run_step "Run install/payload bootstrap smoke" python3 "$ROOT_DIR/scripts/check-install-payload-bundle-smoke.py"

echo "[release-preflight] All checks passed."
