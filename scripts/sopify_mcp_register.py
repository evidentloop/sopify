#!/usr/bin/env python3
"""Register the repo-local Sopify MCP server with a supported host.

The S3.2 pilot is intentionally Codex-first and delegates config writes to the
official ``codex mcp`` CLI. It does not install dependencies or edit TOML.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Callable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_NAME = "sopify"
PYTHON_PROBE = """
import importlib.metadata
import json
import sys

import mcp  # noqa: F401
from mcp.server.fastmcp import FastMCP  # noqa: F401

print(json.dumps({
    "python_version": list(sys.version_info[:3]),
    "mcp_version": importlib.metadata.version("mcp"),
}))
""".strip()

Runner = Callable[..., subprocess.CompletedProcess[str]]


class RegistrationError(RuntimeError):
    """Raised when the registration pilot cannot proceed safely."""


def _run(command: Sequence[str], *, runner: Runner) -> subprocess.CompletedProcess[str]:
    argv = list(command)
    try:
        return runner(
            argv,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        detail = exc.strerror or str(exc)
        raise RegistrationError(f"Failed to start command {argv[0]!r}: {detail}") from exc


def _probe_python(python_executable: Path, *, runner: Runner) -> dict[str, Any]:
    completed = _run((str(python_executable), "-c", PYTHON_PROBE), runner=runner)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RegistrationError(f"Python/MCP preflight failed: {detail}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RegistrationError("Python/MCP preflight returned invalid JSON") from exc
    version = payload.get("python_version")
    if not isinstance(version, list) or tuple(version[:2]) < (3, 11):
        raise RegistrationError(f"Python >=3.11 is required, got: {version}")
    mcp_version = payload.get("mcp_version")
    try:
        mcp_major, mcp_minor = (int(part) for part in str(mcp_version).split(".")[:2])
    except (TypeError, ValueError):
        raise RegistrationError(f"Invalid MCP SDK version: {mcp_version}") from None
    if mcp_major != 1 or mcp_minor < 27:
        raise RegistrationError(f"MCP SDK >=1.27,<2 is required, got: {mcp_version}")
    return payload


def _get_server(codex_executable: str, *, runner: Runner) -> dict[str, Any] | None:
    completed = _run((codex_executable, "mcp", "get", SERVER_NAME, "--json"), runner=runner)
    if completed.returncode == 0:
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RegistrationError("codex mcp get returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise RegistrationError("codex mcp get did not return an object")
        return payload

    detail = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
    if f"No MCP server named '{SERVER_NAME}' found" in detail:
        return None
    raise RegistrationError(f"codex mcp get failed: {detail or 'unknown error'}")


def _server_matches(existing: dict[str, Any], *, python_executable: Path, server_script: Path) -> bool:
    transport = existing.get("transport")
    if existing.get("enabled") is False:
        return False
    if not isinstance(transport, dict) or transport.get("type") != "stdio":
        return False
    return transport.get("command") == str(python_executable) and transport.get("args") == [str(server_script)]


def register_mcp_config(
    host_id: str = "codex",
    *,
    apply: bool = False,
    python_executable: str | Path = sys.executable,
    repo_root: str | Path = REPO_ROOT,
    codex_executable: str | None = None,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    """Plan or apply the minimal Codex-first MCP registration."""
    if host_id != "codex":
        raise RegistrationError(f"Unsupported host for S3.2 pilot: {host_id}")

    resolved_repo = Path(repo_root).expanduser().resolve()
    server_script = resolved_repo / "scripts" / "sopify_mcp_server.py"
    if not server_script.is_file():
        raise RegistrationError(f"Sopify MCP server not found: {server_script}")

    resolved_python = Path(python_executable).expanduser().resolve()
    python_info = _probe_python(resolved_python, runner=runner)

    resolved_codex = codex_executable or shutil.which("codex")
    if not resolved_codex:
        raise RegistrationError("Codex CLI was not found on PATH")

    add_command = [
        resolved_codex,
        "mcp",
        "add",
        SERVER_NAME,
        "--",
        str(resolved_python),
        str(server_script),
    ]
    existing = _get_server(resolved_codex, runner=runner)
    base = {
        "host": host_id,
        "server": SERVER_NAME,
        "python": str(resolved_python),
        "python_version": ".".join(str(value) for value in python_info["python_version"]),
        "mcp_version": str(python_info["mcp_version"]),
        "server_script": str(server_script),
        "command": add_command,
        "apply": apply,
    }

    if existing is not None:
        if _server_matches(existing, python_executable=resolved_python, server_script=server_script):
            return {**base, "status": "noop"}
        transport = existing.get("transport") if isinstance(existing.get("transport"), dict) else {}
        return {
            **base,
            "status": "conflict",
            "existing": {
                "enabled": existing.get("enabled"),
                "type": transport.get("type"),
                "command": transport.get("command"),
                "args": transport.get("args"),
            },
        }

    if not apply:
        return {**base, "status": "planned"}

    completed = _run(add_command, runner=runner)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise RegistrationError(f"codex mcp add failed: {detail}")

    registered = _get_server(resolved_codex, runner=runner)
    if registered is None or not _server_matches(
        registered,
        python_executable=resolved_python,
        server_script=server_script,
    ):
        raise RegistrationError("Codex registration verification did not match the requested server")
    return {**base, "status": "registered"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan or apply the repo-local Sopify MCP registration.")
    parser.add_argument("--host", default="codex", choices=("codex",))
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Existing Python >=3.11 with mcp[cli]>=1.27,<2 installed.",
    )
    parser.add_argument("--apply", action="store_true", help="Apply with `codex mcp add`; default is dry-run.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = register_mcp_config(
            args.host,
            apply=args.apply,
            python_executable=args.python,
        )
    except RegistrationError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "conflict" else 0


if __name__ == "__main__":
    raise SystemExit(main())
