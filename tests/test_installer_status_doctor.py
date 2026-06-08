# Test classification: distribution
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from installer.hosts import get_host_capability, iter_declared_hosts, iter_installable_hosts
from installer.hosts.base import install_host_assets
from installer.hosts.claude import CLAUDE_ADAPTER
from installer.hosts.codex import CODEX_ADAPTER
from installer.inspection import build_doctor_payload, build_status_payload, render_doctor_text, render_status_text
from installer.payload import _REQUIRED_BUNDLE_CAPABILITIES, install_global_payload, run_workspace_bootstrap
from installer.validate import validate_host_install, validate_payload_install
from scripts.sopify_doctor import main as doctor_main
from scripts.sopify_status import main as status_main


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _seed_workspace_state(workspace_root: Path) -> None:
    state_root = workspace_root / ".sopify-skills" / "state"
    _write_json(
        state_root / "active_plan.json",
        {"plan_id": "20260320_helloagents_integration_enhancements"},
    )
    _write_json(
        state_root / "current_handoff.json",
        {"required_host_action": "continue_host_develop"},
    )



class HostCapabilityRegistryTests(unittest.TestCase):
    def test_registry_returns_complete_capabilities_for_declared_hosts(self) -> None:
        codex = get_host_capability("codex")
        claude = get_host_capability("claude")

        self.assertEqual(codex.support_tier.value, "deep_verified")
        self.assertEqual(claude.support_tier.value, "deep_verified")
        self.assertTrue(codex.install_enabled)
        self.assertTrue(claude.install_enabled)
        self.assertIn("smoke_verified", [feature.value for feature in claude.verified_features])

        retired_host = "tr" + "ae-cn"
        with self.assertRaisesRegex(ValueError, f"Unsupported host capability: {retired_host}"):
            get_host_capability(retired_host)

    def test_installable_hosts_only_return_install_enabled_entries(self) -> None:
        installable = [capability.host_id for capability in iter_installable_hosts()]
        declared = [capability.host_id for capability in iter_declared_hosts()]

        self.assertEqual(set(installable), {"codex", "claude", "copilot"})
        self.assertEqual(set(declared), {"codex", "claude", "copilot"})


class StatusDoctorContractTests(unittest.TestCase):
    def test_status_payload_supports_workspace_not_requested(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            home_root = Path(home_dir)

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)

            payload = build_status_payload(home_root=home_root, workspace_root=None)

            self.assertFalse(payload["workspace_state"]["requested"])
            self.assertEqual(payload["workspace_state"]["bootstrap_mode"], "on_first_project_trigger")
            self.assertEqual(payload["hosts"][0]["state"]["workspace_bundle_healthy"], "not_requested")
            self.assertEqual(payload["hosts"][0]["payload_bundle"]["source_kind"], "global_active")
            self.assertEqual(payload["hosts"][0]["payload_bundle"]["reason_code"], "PAYLOAD_BUNDLE_READY")
            rendered = render_status_text(payload)
            self.assertIn("requested: no", rendered)
            self.assertIn("will bootstrap on first project trigger", rendered)
            self.assertIn("payload_bundle=global_active (PAYLOAD_BUNDLE_READY)", rendered)

    def test_doctor_payload_supports_workspace_not_requested(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            home_root = Path(home_dir)

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)

            payload = build_doctor_payload(home_root=home_root, workspace_root=None)

            workspace_check = next(
                check
                for check in payload["checks"]
                if check["host_id"] == "codex" and check["check_id"] == "workspace_bundle_manifest"
            )
            self.assertEqual(workspace_check["status"], "skip")
            self.assertEqual(workspace_check["reason_code"], "WORKSPACE_NOT_REQUESTED")
            self.assertEqual(
                workspace_check["recommendation"],
                "Workspace bootstrap was not requested. Trigger Sopify in a project workspace to bootstrap on demand.",
            )
            payload_bundle_check = next(
                check
                for check in payload["checks"]
                if check["host_id"] == "codex" and check["check_id"] == "payload_bundle_resolution"
            )
            self.assertEqual(payload_bundle_check["status"], "pass")
            self.assertEqual(payload_bundle_check["reason_code"], "PAYLOAD_BUNDLE_READY")
            self.assertEqual(payload_bundle_check["source_kind"], "global_active")

    def test_status_and_doctor_surface_legacy_payload_bundle_layout(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            home_root = Path(home_dir)

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)

            payload_root = CODEX_ADAPTER.payload_root(home_root)
            payload_manifest = json.loads((payload_root / "payload-manifest.json").read_text(encoding="utf-8"))
            active_version = payload_manifest["active_version"]
            legacy_bundle_root = payload_root / "bundle"
            shutil.copytree(payload_root / "bundles" / active_version, legacy_bundle_root)
            _write_json(
                payload_root / "payload-manifest.json",
                {
                    "schema_version": "1",
                    "payload_version": active_version,
                    "bundle_version": active_version,
                    "bundle_manifest": "bundle/manifest.json",
                    "bundle_template_dir": "bundle",
                    "helper_entry": "helpers/bootstrap_workspace.py",
                },
            )

            status_payload = build_status_payload(home_root=home_root, workspace_root=None)
            self.assertEqual(status_payload["hosts"][0]["payload_bundle"]["source_kind"], "legacy_layout")
            self.assertEqual(status_payload["hosts"][0]["payload_bundle"]["reason_code"], "PAYLOAD_BUNDLE_READY")
            rendered = render_status_text(status_payload)
            self.assertIn("payload_bundle=legacy_layout (PAYLOAD_BUNDLE_READY)", rendered)
            self.assertNotIn("payload_outcome:", rendered)

            doctor_payload = build_doctor_payload(home_root=home_root, workspace_root=None)
            payload_bundle_check = next(
                check
                for check in doctor_payload["checks"]
                if check["host_id"] == "codex" and check["check_id"] == "payload_bundle_resolution"
            )
            self.assertEqual(payload_bundle_check["status"], "pass")
            self.assertEqual(payload_bundle_check["reason_code"], "PAYLOAD_BUNDLE_READY")
            self.assertEqual(payload_bundle_check["source_kind"], "legacy_layout")
            self.assertNotIn("outcome:", render_doctor_text(doctor_payload))

    def test_status_and_doctor_fail_closed_for_non_object_payload_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            home_root = Path(home_dir)

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)

            payload_root = CODEX_ADAPTER.payload_root(home_root)
            (payload_root / "payload-manifest.json").write_text("[1]", encoding="utf-8")

            status_payload = build_status_payload(home_root=home_root, workspace_root=None)
            self.assertEqual(status_payload["hosts"][0]["payload_bundle"]["source_kind"], "unresolved")
            self.assertEqual(status_payload["hosts"][0]["payload_bundle"]["reason_code"], "GLOBAL_INDEX_CORRUPTED")
            self.assertEqual(status_payload["hosts"][0]["payload_bundle"]["primary_code"], "global_index_corrupted")
            self.assertEqual(status_payload["hosts"][0]["payload_bundle"]["action_level"], "fail_closed")
            self.assertIn("payload_outcome: global_index_corrupted [fail_closed]", render_status_text(status_payload))

            doctor_payload = build_doctor_payload(home_root=home_root, workspace_root=None)
            payload_bundle_check = next(
                check
                for check in doctor_payload["checks"]
                if check["host_id"] == "codex" and check["check_id"] == "payload_bundle_resolution"
            )
            self.assertEqual(payload_bundle_check["status"], "fail")
            self.assertEqual(payload_bundle_check["reason_code"], "GLOBAL_INDEX_CORRUPTED")
            self.assertEqual(payload_bundle_check["source_kind"], "unresolved")
            self.assertEqual(payload_bundle_check["primary_code"], "global_index_corrupted")
            self.assertEqual(payload_bundle_check["action_level"], "fail_closed")
            self.assertIn("outcome: global_index_corrupted [fail_closed]", render_doctor_text(doctor_payload))

    def test_status_and_doctor_fail_closed_for_versioned_layout_missing_active_version(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            home_root = Path(home_dir)

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)

            payload_root = CODEX_ADAPTER.payload_root(home_root)
            payload_manifest = json.loads((payload_root / "payload-manifest.json").read_text(encoding="utf-8"))
            payload_manifest.pop("active_version", None)
            (payload_root / "payload-manifest.json").write_text(
                json.dumps(payload_manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            status_payload = build_status_payload(home_root=home_root, workspace_root=None)
            self.assertEqual(status_payload["hosts"][0]["payload_bundle"]["source_kind"], "global_active")
            self.assertEqual(status_payload["hosts"][0]["payload_bundle"]["reason_code"], "GLOBAL_INDEX_CORRUPTED")

            doctor_payload = build_doctor_payload(home_root=home_root, workspace_root=None)
            payload_bundle_check = next(
                check
                for check in doctor_payload["checks"]
                if check["host_id"] == "codex" and check["check_id"] == "payload_bundle_resolution"
            )
            self.assertEqual(payload_bundle_check["status"], "fail")
            self.assertEqual(payload_bundle_check["reason_code"], "GLOBAL_INDEX_CORRUPTED")
            self.assertEqual(payload_bundle_check["source_kind"], "global_active")

    def test_status_json_contains_required_contract_and_workspace_state(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as workspace_dir:
            home_root = Path(home_dir)
            workspace_root = Path(workspace_dir)
            _seed_workspace_state(workspace_root)

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)
            validate_host_install(CODEX_ADAPTER, home_root=home_root)
            validate_payload_install(CODEX_ADAPTER.payload_root(home_root))

            payload = build_status_payload(home_root=home_root, workspace_root=workspace_root)

            self.assertEqual(payload["schema_version"], "2")
            self.assertIn("hosts", payload)
            self.assertIn("state", payload)
            self.assertIn("workspace_state", payload)
            self.assertEqual(payload["workspace_state"]["active_plan"], "20260320_helloagents_integration_enhancements")
            self.assertEqual(payload["workspace_state"]["pending_checkpoint"], "continue_host_develop")
            self.assertEqual(payload["state"]["overall_status"], "partial")
            self.assertEqual(payload["hosts"][0]["verified_features"], ["prompt_install", "payload_install", "workspace_bootstrap", "preferences_preload", "handoff_first", "host_bridge", "smoke_verified"])
            self.assertEqual(
                set(payload["hosts"][0]["state"].keys()),
                {"installed", "configured", "workspace_bundle_healthy"},
            )
            self.assertIn("workspace_bundle", payload["hosts"][0])
            self.assertEqual(payload["hosts"][0]["state"]["configured"], "yes")
            self.assertEqual(payload["hosts"][0]["state"]["workspace_bundle_healthy"], "no")
            self.assertNotIn("verified", payload["hosts"][0]["state"])

    def test_doctor_json_contains_reason_codes_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as workspace_dir:
            home_root = Path(home_dir)
            workspace_root = Path(workspace_dir)

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)

            payload = build_doctor_payload(home_root=home_root, workspace_root=workspace_root)

            self.assertEqual(payload["schema_version"], "1")
            self.assertIn("checks", payload)
            self.assertIn("summary", payload)
            self.assertTrue(payload["checks"])
            check = payload["checks"][0]
            self.assertIn("check_id", check)
            self.assertIn("status", check)
            self.assertIn("reason_code", check)
            self.assertIn(check["reason_code"], {"ok", "MISSING_REQUIRED_FILE", "MISSING_BUNDLE", "UNEXPECTED_ERROR"})


    def test_status_json_reports_ready_when_workspace_bundle_is_healthy(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as workspace_dir:
            home_root = Path(home_dir)
            workspace_root = Path(workspace_dir)

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)
            run_workspace_bootstrap(CODEX_ADAPTER.payload_root(home_root), workspace_root)

            payload = build_status_payload(home_root=home_root, workspace_root=workspace_root)

            self.assertEqual(payload["schema_version"], "2")
            self.assertEqual(payload["state"]["overall_status"], "ready")
            self.assertEqual(payload["state"]["workspace_bundle_healthy_hosts"], ["codex"])
            self.assertEqual(payload["hosts"][0]["state"]["workspace_bundle_healthy"], "yes")

    def test_status_and_doctor_treat_stub_only_workspace_as_ready_when_global_bundle_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as workspace_dir:
            home_root = Path(home_dir)
            workspace_root = Path(workspace_dir)

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)
            run_workspace_bootstrap(CODEX_ADAPTER.payload_root(home_root), workspace_root)

            bundle_root = workspace_root / ".sopify-skills"
            for name in ("sopify_contracts", "sopify_writer", "runtime", "scripts", "tests"):
                target = bundle_root / name
                if target.exists():
                    import shutil

                    shutil.rmtree(target)

            status_payload = build_status_payload(home_root=home_root, workspace_root=workspace_root)
            self.assertEqual(status_payload["hosts"][0]["state"]["workspace_bundle_healthy"], "yes")
            self.assertEqual(status_payload["hosts"][0]["workspace_bundle"]["primary_code"], "stub_selected")
            self.assertEqual(status_payload["hosts"][0]["workspace_bundle"]["action_level"], "continue")
            self.assertIn("workspace_outcome: stub_selected [continue]", render_status_text(status_payload))

            doctor_payload = build_doctor_payload(home_root=home_root, workspace_root=workspace_root)
            workspace_check = next(
                check
                for check in doctor_payload["checks"]
                if check["host_id"] == "codex" and check["check_id"] == "workspace_bundle_manifest"
            )
            self.assertEqual(workspace_check["status"], "pass")
            self.assertEqual(workspace_check["reason_code"], "STUB_SELECTED")
            self.assertEqual(workspace_check["primary_code"], "stub_selected")
            self.assertEqual(workspace_check["action_level"], "continue")
            self.assertIn("NON_GIT_WORKSPACE", workspace_check["evidence"])
            self.assertIn("ignore_mode=noop", workspace_check["evidence"])
            self.assertIn("outcome: stub_selected [continue]", render_doctor_text(doctor_payload))

    def test_doctor_resolves_workspace_capabilities_from_global_bundle_when_workspace_manifest_is_stub_only(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as workspace_dir:
            home_root = Path(home_dir)
            workspace_root = Path(workspace_dir)

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)
            run_workspace_bootstrap(CODEX_ADAPTER.payload_root(home_root), workspace_root)

            workspace_manifest = json.loads((workspace_root / ".sopify-skills" / "sopify.json").read_text(encoding="utf-8"))
            self.assertEqual(workspace_manifest["capabilities"], [])
            self.assertNotIn("limits", workspace_manifest)

            doctor_payload = build_doctor_payload(home_root=home_root, workspace_root=workspace_root)
            handoff_check = next(
                check
                for check in doctor_payload["checks"]
                if check["host_id"] == "codex" and check["check_id"] == "workspace_handoff_first"
            )
            preload_check = next(
                check
                for check in doctor_payload["checks"]
                if check["host_id"] == "codex" and check["check_id"] == "workspace_preferences_preload"
            )
            self.assertEqual(handoff_check["status"], "pass")
            self.assertEqual(handoff_check["reason_code"], "ok")
            self.assertEqual(preload_check["status"], "pass")
            self.assertEqual(preload_check["reason_code"], "ok")

    def test_doctor_fail_closes_when_selected_global_bundle_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as workspace_dir:
            home_root = Path(home_dir)
            workspace_root = Path(workspace_dir)

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)
            run_workspace_bootstrap(CODEX_ADAPTER.payload_root(home_root), workspace_root)

            payload_root = CODEX_ADAPTER.payload_root(home_root)
            payload_manifest = json.loads((payload_root / "payload-manifest.json").read_text(encoding="utf-8"))
            selected_version = str(payload_manifest["active_version"])
            selected_bundle_root = payload_root / "bundles" / selected_version
            shutil.rmtree(selected_bundle_root)

            doctor_payload = build_doctor_payload(home_root=home_root, workspace_root=workspace_root)
            workspace_check = next(
                check
                for check in doctor_payload["checks"]
                if check["host_id"] == "codex" and check["check_id"] == "workspace_bundle_manifest"
            )
            handoff_check = next(
                check
                for check in doctor_payload["checks"]
                if check["host_id"] == "codex" and check["check_id"] == "workspace_handoff_first"
            )
            preload_check = next(
                check
                for check in doctor_payload["checks"]
                if check["host_id"] == "codex" and check["check_id"] == "workspace_preferences_preload"
            )
            payload_bundle_check = next(
                check
                for check in doctor_payload["checks"]
                if check["host_id"] == "codex" and check["check_id"] == "payload_bundle_resolution"
            )

            self.assertEqual(workspace_check["reason_code"], "GLOBAL_BUNDLE_MISSING")
            self.assertEqual(handoff_check["status"], "fail")
            self.assertEqual(handoff_check["reason_code"], "GLOBAL_BUNDLE_MISSING")
            self.assertEqual(preload_check["status"], "fail")
            self.assertEqual(preload_check["reason_code"], "GLOBAL_BUNDLE_MISSING")
            self.assertEqual(payload_bundle_check["reason_code"], "GLOBAL_BUNDLE_MISSING")

    def test_doctor_recommends_on_demand_bootstrap_without_public_workspace_flag(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as workspace_dir:
            home_root = Path(home_dir)
            workspace_root = Path(workspace_dir)

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)

            doctor_payload = build_doctor_payload(home_root=home_root, workspace_root=workspace_root)
            workspace_check = next(
                check
                for check in doctor_payload["checks"]
                if check["host_id"] == "codex" and check["check_id"] == "workspace_bundle_manifest"
            )

            self.assertEqual(workspace_check["reason_code"], "MISSING_BUNDLE")
            self.assertIn("Trigger Sopify there to bootstrap on demand", workspace_check["recommendation"])
            self.assertNotIn("--workspace", workspace_check["recommendation"])

    def test_status_and_doctor_surface_partial_bundle_damage_as_replace_required(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as workspace_dir:
            home_root = Path(home_dir)
            workspace_root = Path(workspace_dir)

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)
            run_workspace_bootstrap(CODEX_ADAPTER.payload_root(home_root), workspace_root)

            payload_root = CODEX_ADAPTER.payload_root(home_root)
            payload_manifest = json.loads((payload_root / "payload-manifest.json").read_text(encoding="utf-8"))
            active_version = payload_manifest["active_version"]
            bundle_root = workspace_root / ".sopify-skills"
            for name in ("sopify_contracts", "sopify_writer", "runtime", "scripts", "tests"):
                shutil.copytree(payload_root / "bundles" / active_version / name, bundle_root / name)
            (bundle_root / "scripts" / "runtime_gate.py").unlink()

            doctor_payload = build_doctor_payload(home_root=home_root, workspace_root=workspace_root)
            workspace_check = next(
                check
                for check in doctor_payload["checks"]
                if check["host_id"] == "codex" and check["check_id"] == "workspace_bundle_manifest"
            )
            self.assertEqual(workspace_check["status"], "pass")
            self.assertEqual(workspace_check["reason_code"], "STUB_SELECTED")
            self.assertIn("NON_GIT_WORKSPACE", workspace_check["evidence"])
            self.assertNotIn("recommendation", workspace_check)

    def test_status_cli_json_output_contains_hosts_and_workspace_state(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as workspace_dir:
            home_root = Path(home_dir)
            workspace_root = Path(workspace_dir)
            _seed_workspace_state(workspace_root)

            install_host_assets(CLAUDE_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="EN")
            install_global_payload(CLAUDE_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)

            completed = _run_script(
                status_main,
                [
                    "--format",
                    "json",
                    "--home-root",
                    str(home_root),
                    "--workspace-root",
                    str(workspace_root),
                ],
            )
            payload = json.loads(completed)
            self.assertEqual(payload["schema_version"], "2")
            self.assertIn("hosts", payload)
            self.assertIn("workspace_state", payload)

    def test_doctor_cli_json_output_contains_checks_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as workspace_dir:
            home_root = Path(home_dir)
            workspace_root = Path(workspace_dir)

            install_host_assets(CLAUDE_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="EN")
            install_global_payload(CLAUDE_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)

            completed = _run_script(
                doctor_main,
                [
                    "--format",
                    "json",
                    "--home-root",
                    str(home_root),
                    "--workspace-root",
                    str(workspace_root),
                ],
            )
            payload = json.loads(completed)
            self.assertEqual(payload["schema_version"], "1")
            self.assertIn("checks", payload)
            self.assertIn("summary", payload)


    def test_status_text_renders_human_labels_not_raw_taxonomy(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as workspace_dir:
            home_root = Path(home_dir)
            workspace_root = Path(workspace_dir)
            state_root = workspace_root / ".sopify-skills" / "state"
            _write_json(
                state_root / "active_plan.json",
                {"plan_id": "p"},
            )
            _write_json(
                state_root / "current_handoff.json",
                {"required_host_action": "answer_questions"},
            )

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)

            status_payload = build_status_payload(home_root=home_root, workspace_root=workspace_root)
            rendered = render_status_text(status_payload)

            self.assertIn("pending_checkpoint: awaiting supplemental info", rendered)
            self.assertNotIn("answer_questions", rendered)

    def test_status_text_renders_mapped_checkpoint_labels(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as workspace_dir:
            home_root = Path(home_dir)
            workspace_root = Path(workspace_dir)
            _seed_workspace_state(workspace_root)

            install_host_assets(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root, language_directory="CN")
            install_global_payload(CODEX_ADAPTER, repo_root=REPO_ROOT, home_root=home_root)

            status_payload = build_status_payload(home_root=home_root, workspace_root=workspace_root)
            rendered = render_status_text(status_payload)

            self.assertIn("pending_checkpoint: ready to continue", rendered)
            self.assertNotIn("continue_host_develop", rendered)


def _run_script(entrypoint, argv: list[str]) -> str:
    from io import StringIO
    from contextlib import redirect_stdout

    buffer = StringIO()
    with redirect_stdout(buffer):
        exit_code = entrypoint(argv)
    if exit_code != 0:
        raise AssertionError(f"Expected exit code 0, got {exit_code}")
    return buffer.getvalue()


if __name__ == "__main__":
    unittest.main()
