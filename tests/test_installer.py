from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]


class InstallerCliTests(unittest.TestCase):
    def _run_installer(
        self,
        *,
        target: str,
        home_root: Path,
        workspace_root: Path | None = None,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = ["bash", str(REPO_ROOT / "scripts" / "install-sopify.sh"), "--target", target]
        if workspace_root is not None:
            command.extend(["--workspace", str(workspace_root)])
        env = dict(os.environ)
        env["HOME"] = str(home_root)
        return subprocess.run(
            command,
            cwd=str(cwd or REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_installs_codex_cn_with_explicit_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            home_root = temp_root / "home"
            workspace_root = temp_root / "workspace"
            home_root.mkdir()
            workspace_root.mkdir()

            completed = self._run_installer(
                target="codex:zh-CN",
                home_root=home_root,
                workspace_root=workspace_root,
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("target: codex:zh-CN", completed.stdout)
            self.assertTrue((home_root / ".codex" / "AGENTS.md").exists())
            self.assertTrue((home_root / ".codex" / "skills" / "sopify" / "analyze" / "SKILL.md").exists())
            self.assertTrue((home_root / ".codex" / "sopify" / "payload-manifest.json").exists())
            self.assertTrue((home_root / ".codex" / "sopify" / "bundle" / "manifest.json").exists())
            self.assertTrue((home_root / ".codex" / "sopify" / "helpers" / "bootstrap_workspace.py").exists())
            self.assertTrue((workspace_root / ".sopify-runtime" / "manifest.json").exists())
            self.assertTrue((workspace_root / ".sopify-runtime" / "scripts" / "sopify_runtime.py").exists())
            self.assertTrue((workspace_root / ".sopify-runtime" / "tests" / "test_runtime.py").exists())
            self.assertIn("Host:", completed.stdout)
            self.assertIn("Payload:", completed.stdout)
            self.assertIn("Workspace:", completed.stdout)

    def test_installs_claude_en_without_workspace_bootstrap_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            home_root = temp_root / "home"
            workspace_root = temp_root / "workspace"
            home_root.mkdir()
            workspace_root.mkdir()

            completed = self._run_installer(
                target="claude:en-US",
                home_root=home_root,
                cwd=workspace_root,
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertIn("workspace: (not requested)", completed.stdout)
            self.assertTrue((home_root / ".claude" / "CLAUDE.md").exists())
            self.assertTrue((home_root / ".claude" / "skills" / "sopify" / "design" / "SKILL.md").exists())
            self.assertTrue((home_root / ".claude" / "sopify" / "payload-manifest.json").exists())
            self.assertTrue((home_root / ".claude" / "sopify" / "bundle" / "runtime" / "__init__.py").exists())
            self.assertFalse((workspace_root / ".sopify-runtime").exists())
            payload_manifest = json.loads((home_root / ".claude" / "sopify" / "payload-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(payload_manifest["bundle_manifest"], "bundle/manifest.json")
            self.assertEqual(payload_manifest["helper_entry"], "helpers/bootstrap_workspace.py")
            self.assertIn("Runtime smoke check passed:", completed.stdout)
            self.assertIn("workspace bootstrap not requested", completed.stdout)

    def test_global_helper_bootstraps_workspace_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            home_root = temp_root / "home"
            source_workspace = temp_root / "source-workspace"
            target_workspace = temp_root / "target-workspace"
            home_root.mkdir()
            source_workspace.mkdir()
            target_workspace.mkdir()

            completed = self._run_installer(
                target="codex:zh-CN",
                home_root=home_root,
                cwd=source_workspace,
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)

            helper_path = home_root / ".codex" / "sopify" / "helpers" / "bootstrap_workspace.py"
            helper_completed = subprocess.run(
                ["python3", str(helper_path), "--workspace-root", str(target_workspace)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(helper_completed.returncode, 0, msg=helper_completed.stderr)
            payload = json.loads(helper_completed.stdout)
            self.assertEqual(payload["action"], "bootstrapped")
            self.assertEqual(payload["state"], "MISSING")
            self.assertTrue((target_workspace / ".sopify-runtime" / "manifest.json").exists())
            self.assertTrue((target_workspace / ".sopify-runtime" / "scripts" / "sopify_runtime.py").exists())
            self.assertFalse((target_workspace / ".sopify-runtime" / "helpers").exists())

    def test_global_helper_skips_newer_workspace_bundle_without_downgrade(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            home_root = temp_root / "home"
            workspace_root = temp_root / "workspace"
            home_root.mkdir()
            workspace_root.mkdir()

            completed = self._run_installer(
                target="codex:zh-CN",
                home_root=home_root,
                cwd=workspace_root,
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr)

            payload_bundle = home_root / ".codex" / "sopify" / "bundle"
            workspace_bundle = workspace_root / ".sopify-runtime"
            shutil.copytree(payload_bundle, workspace_bundle)
            manifest_path = workspace_bundle / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["bundle_version"] = "9999-01-01"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            helper_path = home_root / ".codex" / "sopify" / "helpers" / "bootstrap_workspace.py"
            helper_completed = subprocess.run(
                ["python3", str(helper_path), "--workspace-root", str(workspace_root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(helper_completed.returncode, 0, msg=helper_completed.stderr)
            payload = json.loads(helper_completed.stdout)
            self.assertEqual(payload["action"], "skipped")
            self.assertEqual(payload["state"], "NEWER_THAN_GLOBAL")
            self.assertEqual(payload["reason_code"], "WORKSPACE_BUNDLE_NEWER_THAN_GLOBAL")
            updated_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(updated_manifest["bundle_version"], "9999-01-01")

    def test_rejects_invalid_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            home_root = temp_root / "home"
            workspace_root = temp_root / "workspace"
            home_root.mkdir()
            workspace_root.mkdir()

            completed = self._run_installer(
                target="codex",
                home_root=home_root,
                workspace_root=workspace_root,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Target must use the format <host:lang>", completed.stderr)


if __name__ == "__main__":
    unittest.main()
