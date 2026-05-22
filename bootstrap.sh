#!/usr/bin/env bash
set -euo pipefail

REPO_OWNER="evidentloop"
REPO_NAME="sopify"
ASSET_NAME="bootstrap.sh"
SOURCE_CHANNEL="dev"
SOURCE_REF="main"

usage() {
  cat <<'EOF'
Usage: bootstrap.sh [init] [--workspace <path>] [--no-copilot]

Initialize a Sopify workspace in your project.

This creates the minimal activation markers so your AI host (Copilot, Codex,
Claude) can discover and use Sopify in this repository.

What it creates:
  .sopify-skills/sopify.json   Workspace marker (version + capabilities)
  .gitignore                   Managed ignore block for transient state
  .github/copilot-instructions.md   Copilot instruction entry (unless --no-copilot)

Options:
  --workspace <path>   Target project directory (default: current directory).
  --no-copilot         Skip Copilot instruction file distribution.
  --ref <tag-or-branch>  Advanced: override the source ref.
  --language <lang>    Output language: en-US or zh-CN (default: auto-detect).
  -h, --help           Show this help.

Examples:
  # Initialize the current directory
  curl -fsSL https://github.com/evidentloop/sopify/releases/latest/download/bootstrap.sh | bash

  # Initialize a specific project
  curl -fsSL https://github.com/evidentloop/sopify/releases/latest/download/bootstrap.sh | bash -s -- init --workspace /path/to/project
EOF
}

fail() {
  local phase="$1"
  local reason_code="$2"
  local detail="$3"
  local next_step="$4"
  {
    echo "Sopify bootstrap failed: $detail"
    echo
    echo "Fix:"
    echo "  $next_step"
    echo
    echo "Diagnostics:"
    echo "  reason_code: $reason_code"
    echo "  phase: $phase"
  } >&2
  exit 1
}

log_step() {
  echo "Sopify: $1" >&2
}

require_command() {
  local command_name="$1"
  local reason_code="$2"
  local next_step="$3"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    fail "preflight" "$reason_code" "Missing required command: $command_name" "$next_step"
  fi
}

# ── Argument parsing ─────────────────────────────────────────────────────

FORWARDED_ARGS=()
REF_OVERRIDE=""
HAS_INIT=false
HAS_WORKSPACE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    init)
      HAS_INIT=true
      shift
      ;;
    --ref)
      if [[ $# -lt 2 || -z "${2:-}" ]]; then
        fail "input" "MISSING_REF_VALUE" '`--ref` requires a value.' "Pass --ref <tag-or-branch>, or omit the flag."
      fi
      REF_OVERRIDE="$2"
      shift 2
      ;;
    --ref=*)
      REF_OVERRIDE="${1#*=}"
      if [[ -z "$REF_OVERRIDE" ]]; then
        fail "input" "MISSING_REF_VALUE" '`--ref` requires a value.' "Pass --ref <tag-or-branch>, or omit the flag."
      fi
      shift
      ;;
    --workspace|--workspace=*|-w)
      HAS_WORKSPACE=true
      FORWARDED_ARGS+=("$1")
      if [[ "$1" != --workspace=* && "$1" != -w ]]; then
        shift
        FORWARDED_ARGS+=("$1")
      elif [[ "$1" == -w ]]; then
        shift
        FORWARDED_ARGS+=("$1")
      fi
      shift
      ;;
    *)
      FORWARDED_ARGS+=("$1")
      shift
      ;;
  esac
done

RESOLVED_REF="${REF_OVERRIDE:-$SOURCE_REF}"
if [[ -z "$RESOLVED_REF" ]]; then
  fail "input" "MISSING_SOURCE_REF" "No source ref was resolved." "Retry with --ref <tag-or-branch>."
fi

# Default to init if no subcommand given
if [[ "$HAS_INIT" != true ]]; then
  FORWARDED_ARGS=("init" "${FORWARDED_ARGS[@]}")
fi

# Default workspace to current directory if not specified
if [[ "$HAS_WORKSPACE" != true ]]; then
  FORWARDED_ARGS+=("--workspace" ".")
fi

# ── Download and run ─────────────────────────────────────────────────────

log_step "Checking requirements..."
require_command "curl" "MISSING_CURL" "Install curl, or download the release manually."
require_command "tar" "MISSING_TAR" "Install tar."
require_command "python3" "MISSING_PYTHON3" "Install Python 3, then rerun."

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/sopify-bootstrap.XXXXXX")"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

ARCHIVE_URL="https://codeload.github.com/${REPO_OWNER}/${REPO_NAME}/tar.gz/${RESOLVED_REF}"
ARCHIVE_PATH="$TMP_DIR/source.tar.gz"

log_step "Downloading Sopify source (${RESOLVED_REF})..."
if ! curl -fsSL "$ARCHIVE_URL" -o "$ARCHIVE_PATH"; then
  fail "download" "SOURCE_FETCH_FAILED" "Failed to download source archive: $ARCHIVE_URL" "Check network access and verify the ref exists."
fi

log_step "Unpacking..."
if ! tar -xzf "$ARCHIVE_PATH" -C "$TMP_DIR"; then
  fail "unpack" "SOURCE_EXTRACT_FAILED" "Failed to extract source archive." "Retry or inspect the downloaded archive."
fi

SOURCE_DIR="$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
if [[ -z "$SOURCE_DIR" || ! -d "$SOURCE_DIR" ]]; then
  fail "unpack" "SOURCE_ROOT_MISSING" "Extracted archive has no root directory." "Retry or inspect the downloaded archive."
fi

ENTRYPOINT="$SOURCE_DIR/scripts/sopify_init.py"
if [[ ! -f "$ENTRYPOINT" ]]; then
  fail "unpack" "INIT_ENTRYPOINT_MISSING" "Missing init script: scripts/sopify_init.py" "This release may not support bootstrap. Try a newer version."
fi

log_step "Initializing workspace..."
python3 "$ENTRYPOINT" "${FORWARDED_ARGS[@]}"
exit $?
