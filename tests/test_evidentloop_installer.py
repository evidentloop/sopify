"""Tests for the opt-in EvidentLoop companion installer."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from installer.distribution import (
    _companion_action_lines,
    DistributionError,
    DistributionRequest,
    DistributionSourceMetadata,
    render_distribution_result,
    render_distribution_user_result,
    run_distribution_install,
)
from installer.evidentloop import (
    EVIDENTLOOP_PACKAGE_VERSION,
    EVIDENTLOOP_SKILL_COMMIT,
    EVIDENTLOOP_SKILL_REPOSITORY,
    EVIDENTLOOP_SKILL_TAG,
    SKILLS_CLI_VERSION,
    install_evidentloop_companion,
    prepare_evidentloop_install,
)
from installer.hosts.base import HostAdapter
from installer.hosts.claude import CLAUDE_ADAPTER
from installer.hosts.codex import CODEX_ADAPTER
from installer.hosts.copilot import COPILOT_ADAPTER
from installer.hosts.qoder import QODER_ADAPTER
from installer.models import EvidentLoopInstallResult, InstallError
from scripts.install_sopify import build_parser, run_install


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPATIBLE_SKILL = """\
---
name: evidentloop
---
Require `package_version` equal to `0.1.0a2`, `schema_version` equal to `0.4`, and `prompt_version` equal to `v0.5`.
Read references/codex-cli-isolation.md before running the CLI.
"""


def _completed(
    argv: list[str],
    *,
    stdout: str = "",
    returncode: int = 0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(argv, returncode, stdout=stdout, stderr="")


def _write_compatible_skill(skill_dir: Path) -> None:
    (skill_dir / "references").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(COMPATIBLE_SKILL, encoding="utf-8")
    (skill_dir / "references" / "codex-cli-isolation.md").write_text(
        "# CLI isolation\n",
        encoding="utf-8",
    )


class EvidentLoopInstallerTests(unittest.TestCase):
    def test_versions_source_and_host_native_paths_are_fixed(self) -> None:
        self.assertEqual(EVIDENTLOOP_PACKAGE_VERSION, "0.1.0a2")
        self.assertEqual(
            EVIDENTLOOP_SKILL_COMMIT,
            "fcefb77083d32b034e56b04dcd085dcf5a835550",
        )
        self.assertEqual(EVIDENTLOOP_SKILL_TAG, "v0.1.0a2")
        self.assertEqual(
            EVIDENTLOOP_SKILL_REPOSITORY,
            "https://github.com/evidentloop/evidentloop.git",
        )
        self.assertEqual(SKILLS_CLI_VERSION, "1.5.9")

        home = Path("/home/test")
        workspace = Path("/workspace/project")
        expected = {
            CODEX_ADAPTER: ("codex", home / ".agents/skills/evidentloop"),
            CLAUDE_ADAPTER: ("claude-code", home / ".claude/skills/evidentloop"),
            QODER_ADAPTER: ("qoder", home / ".qoder/skills/evidentloop"),
            COPILOT_ADAPTER: (
                "github-copilot",
                workspace / ".github/skills/evidentloop",
            ),
        }
        for adapter, (agent, path) in expected.items():
            with self.subTest(host=adapter.host_name):
                self.assertEqual(adapter.skills_cli_agent, agent)
                self.assertEqual(
                    adapter.skill_install_path(
                        home_root=home,
                        workspace_root=workspace,
                        skill_name="evidentloop",
                    ),
                    path,
                )

        with self.assertRaisesRegex(InstallError, "requires a workspace"):
            COPILOT_ADAPTER.skill_install_path(
                home_root=home,
                workspace_root=None,
                skill_name="evidentloop",
            )

    def test_flag_is_disabled_by_default_and_does_no_companion_work(self) -> None:
        parser = build_parser()
        self.assertFalse(parser.parse_args(["--target", "codex:en-US"]).with_evidentloop)
        self.assertTrue(
            parser.parse_args(
                ["--target", "codex:en-US", "--with-evidentloop"]
            ).with_evidentloop
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch("scripts.install_sopify.prepare_evidentloop_install") as prepare,
                patch("scripts.install_sopify.install_evidentloop_companion") as install,
            ):
                result = run_install(
                    target_value="codex:en-US",
                    workspace_value=None,
                    repo_root=REPO_ROOT,
                    home_root=Path(temp_dir),
                )

        prepare.assert_not_called()
        install.assert_not_called()
        self.assertIsNone(result.evidentloop_install)

    def test_missing_mapping_stops_before_command_lookup(self) -> None:
        adapter = HostAdapter(
            host_name="future-host",
            destination_dirname=".future",
            header_filename="AGENTS.md",
        )
        with patch("installer.evidentloop.shutil.which") as which:
            with self.assertRaisesRegex(InstallError, "missing Skill install mapping"):
                prepare_evidentloop_install(adapter, home_root=Path("/home/test"))
        which.assert_not_called()

    def test_compatible_components_are_reused_without_uv_or_npx(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            skill_dir = CODEX_ADAPTER.skill_install_path(
                home_root=home,
                workspace_root=None,
                skill_name="evidentloop",
            )
            _write_compatible_skill(skill_dir)

            def fake_which(name: str) -> str | None:
                return {
                    "evidentloop": "/tools/evidentloop",
                    "git": "/tools/git",
                }.get(name)

            with (
                patch("installer.evidentloop.shutil.which", side_effect=fake_which),
                patch(
                    "installer.evidentloop.subprocess.run",
                    side_effect=self._compatible_runner,
                ),
            ):
                plan = prepare_evidentloop_install(CODEX_ADAPTER, home_root=home)
                result = install_evidentloop_companion(plan)

        self.assertFalse(plan.install_cli)
        self.assertFalse(plan.install_skill)
        self.assertEqual((result.cli_action, result.skill_action), ("reused", "reused"))
        self.assertEqual(result.skill_path, skill_dir / "SKILL.md")

    def test_prerequisites_are_required_only_for_missing_components(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            skill_dir = CODEX_ADAPTER.skill_install_path(
                home_root=home,
                workspace_root=None,
                skill_name="evidentloop",
            )
            _write_compatible_skill(skill_dir)
            with patch("installer.evidentloop.shutil.which", return_value=None):
                with self.assertRaisesRegex(InstallError, r"missing required command\(s\): uv$"):
                    prepare_evidentloop_install(CODEX_ADAPTER, home_root=home)

        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            def fake_which(name: str) -> str | None:
                return {
                    "evidentloop": "/tools/evidentloop",
                    "git": "/tools/git",
                }.get(name)

            with (
                patch("installer.evidentloop.shutil.which", side_effect=fake_which),
                patch(
                    "installer.evidentloop.subprocess.run",
                    side_effect=self._compatible_runner,
                ),
            ):
                with self.assertRaisesRegex(InstallError, r"missing required command\(s\): npx$"):
                    prepare_evidentloop_install(CODEX_ADAPTER, home_root=home)

    def test_missing_prerequisite_does_not_undo_sopify_install(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            with patch("installer.evidentloop.shutil.which", return_value=None):
                with self.assertRaisesRegex(
                    InstallError,
                    "Sopify core installation completed.*EvidentLoop was not installed",
                ):
                    run_install(
                        target_value="codex:en-US",
                        workspace_value=None,
                        repo_root=REPO_ROOT,
                        home_root=home,
                        with_evidentloop=True,
                    )
            self.assertTrue((home / ".codex/AGENTS.md").is_file())

    def test_existing_skill_directory_is_validated_without_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            skill_dir = CODEX_ADAPTER.skill_install_path(
                home_root=home,
                workspace_root=None,
                skill_name="evidentloop",
            )
            skill_dir.mkdir(parents=True)
            entrypoint = skill_dir / "SKILL.md"
            entrypoint.write_text(COMPATIBLE_SKILL, encoding="utf-8")

            with patch("installer.evidentloop.shutil.which") as which:
                with self.assertRaisesRegex(InstallError, "missing referenced file"):
                    prepare_evidentloop_install(CODEX_ADAPTER, home_root=home)
            which.assert_not_called()
            self.assertEqual(entrypoint.read_text(encoding="utf-8"), COMPATIBLE_SKILL)

    def test_incompatible_cli_is_not_replaced(self) -> None:
        def fake_which(name: str) -> str | None:
            return {
                "evidentloop": "/tools/evidentloop",
                "uv": "/tools/uv",
                "npx": "/tools/npx",
            }.get(name)

        def incompatible_runner(
            argv: list[str],
            **_kwargs: object,
        ) -> subprocess.CompletedProcess[str]:
            if argv[1:] == ["doctor", "--json"]:
                return _completed(
                    argv,
                    stdout=json.dumps(
                        {"status": "ok", "python_executable": "/tools/python"}
                    ),
                )
            if "-c" in argv:
                return _completed(
                    argv,
                    stdout=json.dumps(
                        {
                            "package_version": "0.1.0a1",
                            "schema_version": "0.4",
                            "prompt_version": "v0.5",
                        }
                    ),
                )
            raise AssertionError(f"unexpected argv: {argv}")

        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch("installer.evidentloop.shutil.which", side_effect=fake_which),
                patch(
                    "installer.evidentloop.subprocess.run",
                    side_effect=incompatible_runner,
                ) as run,
            ):
                with self.assertRaisesRegex(InstallError, "CLI is incompatible"):
                    prepare_evidentloop_install(
                        CODEX_ADAPTER,
                        home_root=Path(temp_dir),
                    )

        executed = [call.args[0][0] for call in run.call_args_list]
        self.assertNotIn("/tools/uv", executed)
        self.assertNotIn("/tools/npx", executed)

    def test_home_skill_install_uses_fixed_global_command_and_real_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            skill_dir = home / ".agents/skills/evidentloop"
            observed: list[tuple[list[str], dict[str, object]]] = []

            def fake_which(name: str) -> str | None:
                return {
                    "evidentloop": "/tools/evidentloop",
                    "npx": "/tools/npx",
                    "git": "/tools/git",
                }.get(name)

            def fake_run(
                argv: list[str],
                **kwargs: object,
            ) -> subprocess.CompletedProcess[str]:
                observed.append((list(argv), kwargs))
                source_result = self._skill_source_result(argv)
                if source_result is not None:
                    return source_result
                if argv[0] == "/tools/npx":
                    _write_compatible_skill(skill_dir)
                    return _completed(argv)
                return self._compatible_runner(argv, **kwargs)

            with (
                patch("installer.evidentloop.shutil.which", side_effect=fake_which),
                patch("installer.evidentloop.subprocess.run", side_effect=fake_run),
            ):
                plan = prepare_evidentloop_install(CODEX_ADAPTER, home_root=home)
                result = install_evidentloop_companion(plan)
            self.assertTrue((skill_dir / "SKILL.md").is_file())

        npx_argv, npx_kwargs = next(item for item in observed if item[0][0] == "/tools/npx")
        clone_argv = next(
            argv for argv, _kwargs in observed if argv[:2] == ["/tools/git", "clone"]
        )
        self.assertEqual(
            clone_argv[:-1],
            [
                "/tools/git",
                "clone",
                "--quiet",
                "--depth",
                "1",
                "--branch",
                "v0.1.0a2",
                "https://github.com/evidentloop/evidentloop.git",
            ],
        )
        self.assertEqual(Path(clone_argv[-1]).name, "source")
        self.assertEqual(npx_argv[:4], ["/tools/npx", "--yes", "skills@1.5.9", "add"])
        self.assertEqual(Path(npx_argv[4]).parts[-3:], ("source", "skills", "evidentloop"))
        self.assertEqual(npx_argv[5:], ["-g", "-a", "codex", "-y", "--copy"])
        self.assertTrue(Path(str(npx_kwargs["cwd"])).name.startswith("sopify-evidentloop-"))
        self.assertEqual(npx_kwargs["env"]["HOME"], str(home))
        self.assertEqual(npx_kwargs["env"]["DISABLE_TELEMETRY"], "1")
        self.assertEqual(npx_kwargs["env"]["DO_NOT_TRACK"], "1")
        self.assertEqual(result.skill_path, skill_dir / "SKILL.md")

    def test_copilot_install_copies_only_skill_to_project_github_path(self) -> None:
        with (
            tempfile.TemporaryDirectory() as home_dir,
            tempfile.TemporaryDirectory() as workspace_dir,
        ):
            home = Path(home_dir)
            workspace = Path(workspace_dir)
            target = workspace / ".github/skills/evidentloop"
            observed_npx: list[tuple[list[str], Path]] = []

            def fake_which(name: str) -> str | None:
                return {
                    "evidentloop": "/tools/evidentloop",
                    "npx": "/tools/npx",
                    "git": "/tools/git",
                }.get(name)

            def fake_run(
                argv: list[str],
                **kwargs: object,
            ) -> subprocess.CompletedProcess[str]:
                source_result = self._skill_source_result(argv)
                if source_result is not None:
                    return source_result
                if argv[0] == "/tools/npx":
                    staging_root = Path(str(kwargs["cwd"]))
                    observed_npx.append((list(argv), staging_root))
                    _write_compatible_skill(
                        staging_root / ".agents/skills/evidentloop"
                    )
                    (staging_root / "skills-lock.json").write_text(
                        "{}\n",
                        encoding="utf-8",
                    )
                    return _completed(argv)
                return self._compatible_runner(argv, **kwargs)

            with (
                patch("installer.evidentloop.shutil.which", side_effect=fake_which),
                patch("installer.evidentloop.subprocess.run", side_effect=fake_run),
            ):
                plan = prepare_evidentloop_install(
                    COPILOT_ADAPTER,
                    home_root=home,
                    workspace_root=workspace,
                )
                result = install_evidentloop_companion(plan)

            npx_argv, staging_root = observed_npx[0]
            self.assertEqual(
                npx_argv[:4],
                ["/tools/npx", "--yes", "skills@1.5.9", "add"],
            )
            self.assertEqual(
                Path(npx_argv[4]).parts[-3:],
                ("source", "skills", "evidentloop"),
            )
            self.assertEqual(
                npx_argv[5:],
                ["-a", "github-copilot", "-y", "--copy"],
            )
            self.assertNotEqual(staging_root, workspace)
            self.assertTrue((target / "SKILL.md").is_file())
            self.assertTrue(
                (target / "references/codex-cli-isolation.md").is_file()
            )
            self.assertFalse((workspace / ".agents/skills/evidentloop").exists())
            self.assertFalse((workspace / "skills-lock.json").exists())
            self.assertEqual(result.skill_path, target / "SKILL.md")

    def test_missing_cli_installs_without_touching_compatible_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            skill_dir = home / ".agents/skills/evidentloop"
            _write_compatible_skill(skill_dir)
            bin_dir = home / "uv-bin"
            bin_dir.mkdir()
            (bin_dir / "evidentloop").write_text("", encoding="utf-8")
            observed: list[list[str]] = []
            cli_installed = False

            def fake_which(name: str) -> str | None:
                if name == "evidentloop" and cli_installed:
                    return str(bin_dir / "evidentloop")
                return "/tools/uv" if name == "uv" else None

            def fake_run(
                argv: list[str],
                **kwargs: object,
            ) -> subprocess.CompletedProcess[str]:
                nonlocal cli_installed
                observed.append(list(argv))
                if argv[1:] == ["tool", "install", "evidentloop==0.1.0a2"]:
                    cli_installed = True
                    return _completed(argv)
                if argv[1:] == ["tool", "dir", "--bin"]:
                    return _completed(argv, stdout=f"{bin_dir}\n")
                return self._compatible_runner(argv, **kwargs)

            with (
                patch("installer.evidentloop.shutil.which", side_effect=fake_which),
                patch("installer.evidentloop.subprocess.run", side_effect=fake_run),
            ):
                plan = prepare_evidentloop_install(CODEX_ADAPTER, home_root=home)
                result = install_evidentloop_companion(plan)

        self.assertEqual((result.cli_action, result.skill_action), ("installed", "reused"))
        self.assertIn(
            ["/tools/uv", "tool", "install", "evidentloop==0.1.0a2"],
            observed,
        )
        self.assertFalse(any(argv[0].endswith("npx") for argv in observed))

    def test_fresh_cli_stops_when_command_is_not_on_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            skill_dir = home / ".agents/skills/evidentloop"
            _write_compatible_skill(skill_dir)
            bin_dir = home / "uv-bin"
            bin_dir.mkdir()
            (bin_dir / "evidentloop").write_text("", encoding="utf-8")

            def fake_which(name: str) -> str | None:
                return "/tools/uv" if name == "uv" else None

            def fake_run(
                argv: list[str],
                **kwargs: object,
            ) -> subprocess.CompletedProcess[str]:
                if argv[1:] == ["tool", "install", "evidentloop==0.1.0a2"]:
                    return _completed(argv)
                if argv[1:] == ["tool", "dir", "--bin"]:
                    return _completed(argv, stdout=f"{bin_dir}\n")
                return self._compatible_runner(argv, **kwargs)

            with (
                patch("installer.evidentloop.shutil.which", side_effect=fake_which),
                patch("installer.evidentloop.subprocess.run", side_effect=fake_run),
            ):
                plan = prepare_evidentloop_install(CODEX_ADAPTER, home_root=home)
                with self.assertRaisesRegex(
                    InstallError,
                    r"CLI installed.*not discoverable on PATH.*uv tool update-shell",
                ):
                    install_evidentloop_companion(plan)

    def test_changed_skill_tag_stops_before_skills_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            observed: list[list[str]] = []

            def fake_which(name: str) -> str | None:
                return {
                    "evidentloop": "/tools/evidentloop",
                    "npx": "/tools/npx",
                    "git": "/tools/git",
                }.get(name)

            def fake_run(
                argv: list[str],
                **kwargs: object,
            ) -> subprocess.CompletedProcess[str]:
                observed.append(list(argv))
                if argv[:2] == ["/tools/git", "clone"]:
                    _write_compatible_skill(Path(argv[-1]) / "skills/evidentloop")
                    return _completed(argv)
                if argv[0:2] == ["/tools/git", "-C"]:
                    return _completed(argv, stdout="changed-commit\n")
                return self._compatible_runner(argv, **kwargs)

            with (
                patch("installer.evidentloop.shutil.which", side_effect=fake_which),
                patch("installer.evidentloop.subprocess.run", side_effect=fake_run),
            ):
                plan = prepare_evidentloop_install(CODEX_ADAPTER, home_root=home)
                with self.assertRaisesRegex(InstallError, "source commit changed"):
                    install_evidentloop_companion(plan)

        self.assertFalse(any(argv[0] == "/tools/npx" for argv in observed))

    def test_partial_failure_reports_cli_that_was_already_installed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            bin_dir = home / "uv-bin"
            bin_dir.mkdir()
            (bin_dir / "evidentloop").write_text("", encoding="utf-8")
            cli_installed = False

            def fake_which(name: str) -> str | None:
                if name == "evidentloop" and cli_installed:
                    return str(bin_dir / "evidentloop")
                return {
                    "uv": "/tools/uv",
                    "npx": "/tools/npx",
                    "git": "/tools/git",
                }.get(name)

            def fake_run(
                argv: list[str],
                **kwargs: object,
            ) -> subprocess.CompletedProcess[str]:
                nonlocal cli_installed
                if argv[1:] == ["tool", "install", "evidentloop==0.1.0a2"]:
                    cli_installed = True
                    return _completed(argv)
                if argv[1:] == ["tool", "dir", "--bin"]:
                    return _completed(argv, stdout=f"{bin_dir}\n")
                if argv[:2] == ["/tools/git", "clone"]:
                    return _completed(argv, returncode=1)
                return self._compatible_runner(argv, **kwargs)

            with (
                patch("installer.evidentloop.shutil.which", side_effect=fake_which),
                patch("installer.evidentloop.subprocess.run", side_effect=fake_run),
            ):
                plan = prepare_evidentloop_install(CODEX_ADAPTER, home_root=home)
                with self.assertRaisesRegex(
                    InstallError,
                    "CLI installed.*no external files were rolled back",
                ):
                    install_evidentloop_companion(plan)

    def test_core_completion_is_visible_when_companion_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            with (
                patch(
                    "scripts.install_sopify.prepare_evidentloop_install",
                    return_value=object(),
                ),
                patch(
                    "scripts.install_sopify.install_evidentloop_companion",
                    side_effect=InstallError("Skill install failed"),
                ),
            ):
                with self.assertRaisesRegex(
                    InstallError,
                    "Sopify core installation completed.*EvidentLoop was not installed",
                ):
                    run_install(
                        target_value="codex:en-US",
                        workspace_value=None,
                        repo_root=REPO_ROOT,
                        home_root=home,
                        with_evidentloop=True,
                    )
            self.assertTrue((home / ".codex/AGENTS.md").is_file())

    def test_distribution_reports_actions_version_path_and_stable_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            skill_path = home / ".agents/skills/evidentloop/SKILL.md"
            companion = EvidentLoopInstallResult(
                cli_action="installed",
                skill_action="reused",
                package_version="0.1.0a2",
                skill_path=skill_path,
            )
            request = self._request()
            with (
                patch(
                    "scripts.install_sopify.prepare_evidentloop_install",
                    return_value=object(),
                ),
                patch(
                    "scripts.install_sopify.install_evidentloop_companion",
                    return_value=companion,
                ),
            ):
                report = run_distribution_install(
                    request=request,
                    repo_root=REPO_ROOT,
                    home_root=home,
                    install_executor=run_install,
                )

        detailed = render_distribution_result(report)
        user_facing = render_distribution_user_result(report)
        self.assertIn(
            "EvidentLoop CLI (0.1.0a2): installed (tested with this Sopify release)",
            detailed,
        )
        self.assertIn(
            "EvidentLoop Skill: reused (compatibility checked)", detailed
        )
        self.assertIn(f"EvidentLoop Skill path: {skill_path}", detailed)
        self.assertIn(
            "EvidentLoop CLI（0.1.0a2）：已安装（本次 Sopify 发布验证版本）",
            user_facing,
        )
        self.assertIn(f"EvidentLoop Skill 路径：{skill_path}", user_facing)

        copilot_result = EvidentLoopInstallResult(
            cli_action="reused",
            skill_action="installed",
            package_version="0.1.0a2",
            skill_path=home / ".github/skills/evidentloop/SKILL.md",
        )
        copilot_en = "\n".join(
            _companion_action_lines(copilot_result, language="en-US")
        )
        copilot_zh = "\n".join(
            _companion_action_lines(copilot_result, language="zh-CN")
        )
        self.assertIn("review and commit it if your cloud workflow needs it", copilot_en)
        self.assertIn("Sopify will not commit or update it", copilot_en)
        self.assertIn("如需云端使用，请审查后自行提交", copilot_zh)
        self.assertIn("Sopify 不会自动提交或更新", copilot_zh)

        errors = (
            (
                "EvidentLoop companion preflight failed: "
                "missing required command(s): uv",
                "EVIDENTLOOP_PREREQUISITE_MISSING",
            ),
            (
                "Existing EvidentLoop CLI is incompatible",
                "EVIDENTLOOP_INCOMPATIBLE",
            ),
            (
                "Sopify core installation completed, but EvidentLoop was not installed.",
                "EVIDENTLOOP_COMPANION_INCOMPLETE",
            ),
        )
        for message, reason_code in errors:
            with self.subTest(reason_code=reason_code):
                def fail_install(**_kwargs: object) -> object:
                    raise InstallError(message)

                with self.assertRaises(DistributionError) as raised:
                    run_distribution_install(
                        request=self._request(),
                        repo_root=REPO_ROOT,
                        home_root=Path("/tmp/sopify-test-home"),
                        install_executor=fail_install,
                    )
                self.assertEqual(raised.exception.reason_code, reason_code)

    @staticmethod
    def _request() -> DistributionRequest:
        return DistributionRequest(
            target="codex:zh-CN",
            workspace=None,
            ref_override=None,
            interactive=False,
            source_channel="repo-local",
            source_metadata=DistributionSourceMetadata(
                resolved_ref="working-tree",
                asset_name="scripts/install_sopify.py",
            ),
            with_evidentloop=True,
        )

    @staticmethod
    def _versions_json() -> str:
        return json.dumps(
            {
                "package_version": "0.1.0a2",
                "schema_version": "0.4",
                "prompt_version": "v0.5",
            }
        )

    def _compatible_runner(
        self,
        argv: list[str],
        **_kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        if argv[1:] == ["doctor", "--json"]:
            return _completed(
                argv,
                stdout=json.dumps(
                    {"status": "ok", "python_executable": "/tools/python"}
                ),
            )
        if "-c" in argv:
            return _completed(argv, stdout=self._versions_json())
        if argv[-1] == "--help":
            return _completed(argv, stdout="prepare finalize render revise")
        raise AssertionError(f"unexpected argv: {argv}")

    @staticmethod
    def _skill_source_result(
        argv: list[str],
    ) -> subprocess.CompletedProcess[str] | None:
        if argv[:2] == ["/tools/git", "clone"]:
            source_root = Path(argv[-1])
            _write_compatible_skill(source_root / "skills/evidentloop")
            return _completed(argv)
        if argv[0:2] == ["/tools/git", "-C"] and argv[-2:] == ["rev-parse", "HEAD"]:
            return _completed(
                argv,
                stdout="fcefb77083d32b034e56b04dcd085dcf5a835550\n",
            )
        return None


if __name__ == "__main__":
    unittest.main()
