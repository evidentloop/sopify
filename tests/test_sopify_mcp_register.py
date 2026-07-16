# Test classification: contract
from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.sopify_mcp_register import RegistrationError, main, register_mcp_config


PYTHON_INFO = {"python_version": [3, 11, 13], "mcp_version": "1.28.1"}


def _completed(command: list[str], returncode: int = 0, *, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(command, returncode, stdout, stderr)


def _server_payload(python: Path, server_script: Path) -> dict[str, object]:
    return {
        "name": "sopify",
        "enabled": True,
        "transport": {
            "type": "stdio",
            "command": str(python),
            "args": [str(server_script)],
        },
    }


class FakeRunner:
    def __init__(self, responses: list[subprocess.CompletedProcess[str]]) -> None:
        self.responses = responses
        self.commands: list[list[str]] = []

    def __call__(self, command, **_kwargs):
        self.commands.append(list(command))
        if not self.responses:
            raise AssertionError(f"Unexpected command: {command}")
        return self.responses.pop(0)


class SopifyMcpRegisterTests(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path]:
        python = root / "python3"
        server = root / "scripts" / "sopify_mcp_server.py"
        server.parent.mkdir(parents=True)
        server.write_text("# test\n", encoding="utf-8")
        return python.resolve(), server.resolve()

    def test_dry_run_plans_absent_server_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            python, server = self._fixture(root)
            runner = FakeRunner(
                [
                    _completed([], stdout=json.dumps(PYTHON_INFO)),
                    _completed([], 1, stderr="Error: No MCP server named 'sopify' found."),
                ]
            )

            result = register_mcp_config(
                python_executable=python,
                repo_root=root,
                codex_executable="/usr/bin/codex",
                runner=runner,
            )

            self.assertEqual(result["status"], "planned")
            self.assertEqual(result["command"][-2:], [str(python), str(server)])
            self.assertEqual(len(runner.commands), 2)
            self.assertIn("from mcp.server.fastmcp import FastMCP", runner.commands[0][2])

    def test_same_registration_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            python, server = self._fixture(root)
            runner = FakeRunner(
                [
                    _completed([], stdout=json.dumps(PYTHON_INFO)),
                    _completed([], stdout=json.dumps(_server_payload(python, server))),
                ]
            )

            result = register_mcp_config(
                apply=True,
                python_executable=python,
                repo_root=root,
                codex_executable="/usr/bin/codex",
                runner=runner,
            )

            self.assertEqual(result["status"], "noop")
            self.assertEqual(len(runner.commands), 2)

    def test_disabled_registration_is_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            python, server = self._fixture(root)
            disabled = _server_payload(python, server)
            disabled["enabled"] = False
            runner = FakeRunner(
                [
                    _completed([], stdout=json.dumps(PYTHON_INFO)),
                    _completed([], stdout=json.dumps(disabled)),
                ]
            )

            result = register_mcp_config(
                apply=True,
                python_executable=python,
                repo_root=root,
                codex_executable="/usr/bin/codex",
                runner=runner,
            )

            self.assertEqual(result["status"], "conflict")
            self.assertIs(result["existing"]["enabled"], False)
            self.assertEqual(len(runner.commands), 2)

    def test_conflicting_registration_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            python, _server = self._fixture(root)
            conflict = {
                "name": "sopify",
                "transport": {"type": "stdio", "command": "/other/python", "args": ["/other/server.py"]},
            }
            runner = FakeRunner(
                [
                    _completed([], stdout=json.dumps(PYTHON_INFO)),
                    _completed([], stdout=json.dumps(conflict)),
                ]
            )

            result = register_mcp_config(
                apply=True,
                python_executable=python,
                repo_root=root,
                codex_executable="/usr/bin/codex",
                runner=runner,
            )

            self.assertEqual(result["status"], "conflict")
            self.assertEqual(result["existing"]["command"], "/other/python")
            self.assertEqual(len(runner.commands), 2)

    def test_apply_adds_and_verifies_absent_server(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            python, server = self._fixture(root)
            runner = FakeRunner(
                [
                    _completed([], stdout=json.dumps(PYTHON_INFO)),
                    _completed([], 1, stderr="Error: No MCP server named 'sopify' found."),
                    _completed([], stdout="Added global MCP server 'sopify'."),
                    _completed([], stdout=json.dumps(_server_payload(python, server))),
                ]
            )

            result = register_mcp_config(
                apply=True,
                python_executable=python,
                repo_root=root,
                codex_executable="/usr/bin/codex",
                runner=runner,
            )

            self.assertEqual(result["status"], "registered")
            self.assertEqual(runner.commands[2][1:5], ["mcp", "add", "sopify", "--"])

    def test_missing_mcp_dependency_stops_before_codex_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            python, _server = self._fixture(root)
            runner = FakeRunner([_completed([], 1, stderr="ModuleNotFoundError: No module named 'mcp'")])

            with self.assertRaisesRegex(RegistrationError, "Python/MCP preflight failed"):
                register_mcp_config(
                    python_executable=python,
                    repo_root=root,
                    codex_executable="/usr/bin/codex",
                    runner=runner,
                )
            self.assertEqual(len(runner.commands), 1)

    def test_unsupported_mcp_versions_stop_before_codex_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            python, _server = self._fixture(root)
            for version in ("1.26.9", "2.0.0"):
                with self.subTest(version=version):
                    info = {**PYTHON_INFO, "mcp_version": version}
                    runner = FakeRunner([_completed([], stdout=json.dumps(info))])

                    with self.assertRaisesRegex(RegistrationError, "MCP SDK >=1.27,<2 is required"):
                        register_mcp_config(
                            python_executable=python,
                            repo_root=root,
                            codex_executable="/usr/bin/codex",
                            runner=runner,
                        )
                    self.assertEqual(len(runner.commands), 1)

    def test_missing_python_returns_structured_cli_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_python = Path(temp_dir) / "missing-python"
            output = StringIO()

            with redirect_stdout(output):
                exit_code = main(["--python", str(missing_python)])

            self.assertEqual(exit_code, 1)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["status"], "error")
            self.assertIn("Failed to start command", payload["message"])


if __name__ == "__main__":
    unittest.main()
