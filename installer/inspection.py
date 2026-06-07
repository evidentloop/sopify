"""Shared installer inspection helpers for status, doctor, and install surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

from installer.bootstrap_workspace import (
    DIAGNOSTIC_NON_GIT_WORKSPACE,
    REASON_STUB_INVALID,
    REASON_STUB_SELECTED,
    _classify_workspace_bundle,
    _resolve_selected_payload_bundle,
)
from installer.hosts import iter_host_registrations
from installer.hosts.base import HostAdapter, HostRegistration
from installer.models import HostCapability, InstallError
from installer.outcome_contract import annotate_outcome_payload, diagnostic_identifiers_from_evidence, render_outcome_summary
from installer.validate import (
    resolve_payload_bundle_root,
    run_bundle_smoke_check,
    validate_bundle_install,
    validate_host_install,
    validate_payload_install,
    validate_payload_manifests,
    validate_workspace_bundle_manifest,
    validate_workspace_stub_manifest,
)

STATUS_SCHEMA_VERSION = "2"
DOCTOR_SCHEMA_VERSION = "1"
CHECK_PASS = "pass"
CHECK_WARN = "warn"
CHECK_FAIL = "fail"
CHECK_SKIP = "skip"
STATUS_YES = "yes"
STATUS_NO = "no"
STATUS_NOT_REQUESTED = "not_requested"
STATUS_NOT_APPLICABLE = "not_applicable"
REASON_OK = "ok"
REASON_WORKSPACE_NOT_REQUESTED = "WORKSPACE_NOT_REQUESTED"
REASON_PAYLOAD_BUNDLE_READY = "PAYLOAD_BUNDLE_READY"
REASON_GLOBAL_BUNDLE_MISSING = "GLOBAL_BUNDLE_MISSING"
REASON_GLOBAL_BUNDLE_INCOMPATIBLE = "GLOBAL_BUNDLE_INCOMPATIBLE"
REASON_GLOBAL_INDEX_CORRUPTED = "GLOBAL_INDEX_CORRUPTED"
SOURCE_KIND_GLOBAL_ACTIVE = "global_active"
SOURCE_KIND_LEGACY_LAYOUT = "legacy_layout"
SOURCE_KIND_UNRESOLVED = "unresolved"
STATUS_READY_STATES = {"READY", "NEWER_THAN_GLOBAL"}
STATUS_WARN_STATES = {"MISSING", "OUTDATED_COMPATIBLE"}

_CHECKPOINT_LABELS: dict[str, str] = {
    "answer_questions": "awaiting supplemental info",
    "confirm_decision": "awaiting decision confirmation",
    "continue_host_develop": "ready to continue",
    "continue_host_consult": "ready to continue",
}


@dataclass(frozen=True)
class InspectionCheck:
    """One stable inspection result item."""

    check_id: str
    status: str
    reason_code: str
    evidence: tuple[str, ...] = ()
    recommendation: str | None = None
    host_id: str | None = None
    source_kind: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "check_id": self.check_id,
            "status": self.status,
            "reason_code": self.reason_code,
        }
        if self.host_id is not None:
            payload["host_id"] = self.host_id
        if self.source_kind is not None:
            payload["source_kind"] = self.source_kind
        if self.evidence:
            payload["evidence"] = list(self.evidence)
        if self.recommendation:
            payload["recommendation"] = self.recommendation
        return annotate_outcome_payload(payload, reason_code=self.reason_code, message_hint=self.recommendation)


@dataclass(frozen=True)
class PayloadBundleResolution:
    """Stable payload-bundle resolution summary shared by diagnostics surfaces."""

    source_kind: str
    reason_code: str
    status: str
    bundle_root: Path | None = None
    bundle_manifest_path: Path | None = None
    recommendation: str | None = None

    def to_status_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "source_kind": self.source_kind,
            "reason_code": self.reason_code,
        }
        if self.bundle_root is not None:
            payload["bundle_root"] = str(self.bundle_root)
            if self.source_kind == SOURCE_KIND_GLOBAL_ACTIVE:
                payload["selected_version"] = self.bundle_root.name
        if self.bundle_manifest_path is not None:
            payload["bundle_manifest_path"] = str(self.bundle_manifest_path)
        if self.recommendation:
            payload["recommendation"] = self.recommendation
        return annotate_outcome_payload(payload, reason_code=self.reason_code, message_hint=self.recommendation)

    def to_check(self, *, host_id: str) -> InspectionCheck:
        evidence = tuple(
            str(path)
            for path in (self.bundle_manifest_path, self.bundle_root)
            if path is not None
        )
        return InspectionCheck(
            host_id=host_id,
            check_id="payload_bundle_resolution",
            status=self.status,
            reason_code=self.reason_code,
            source_kind=self.source_kind,
            evidence=evidence,
            recommendation=self.recommendation,
        )


@dataclass(frozen=True)
class HostInspection:
    """All shared inspection facts for one host."""

    registration: HostRegistration
    host_prompt: InspectionCheck
    payload: InspectionCheck
    payload_bundle: PayloadBundleResolution
    workspace_bundle: InspectionCheck
    handoff_first: InspectionCheck
    preferences_preload: InspectionCheck
    smoke: InspectionCheck

    @property
    def capability(self) -> HostCapability:
        return self.registration.capability

    @property
    def adapter(self) -> HostAdapter:
        return self.registration.adapter

    def to_status_dict(self) -> dict[str, object]:
        if self.adapter.is_workspace_scope:
            # Workspace-scope hosts (e.g. Copilot): installed == configured == host_prompt present.
            # No HOME payload / bundle / ingress concepts apply.
            installed = self.host_prompt.status == CHECK_PASS
            return {
                **self.capability.to_dict(),
                "state": {
                    "installed": STATUS_YES if installed else STATUS_NO,
                    "configured": STATUS_YES if installed else STATUS_NO,
                    "workspace_bundle_healthy": STATUS_NOT_APPLICABLE,
                },
            }
        configured = self.payload.status == CHECK_PASS
        workspace_bundle_healthy = _check_state_value(self.workspace_bundle)
        return {
            **self.capability.to_dict(),
            "state": {
                "installed": STATUS_YES if self.host_prompt.status == CHECK_PASS else STATUS_NO,
                "configured": STATUS_YES if configured else STATUS_NO,
                "workspace_bundle_healthy": workspace_bundle_healthy,
            },
            "payload_bundle": self.payload_bundle.to_status_dict(),
            "workspace_bundle": self.workspace_bundle.to_dict(),
        }

    def doctor_checks(self) -> tuple[InspectionCheck, ...]:
        if self.adapter.is_workspace_scope:
            return (self.host_prompt,)
        return (
            self.host_prompt,
            self.payload,
            self.payload_bundle.to_check(host_id=self.capability.host_id),
            self.workspace_bundle,
            self.handoff_first,
            self.preferences_preload,
            self.smoke,
        )


def inspect_all_hosts(
    *,
    home_root: Path,
    workspace_root: Path | None,
    include_smoke: bool,
) -> tuple[HostInspection, ...]:
    """Collect shared inspection facts for every declared host."""
    inspections = []
    for registration in iter_host_registrations():
        inspections.append(
            inspect_host(
                registration=registration,
                home_root=home_root,
                workspace_root=workspace_root,
                include_smoke=include_smoke,
            )
        )
    return tuple(inspections)


def inspect_host(
    *,
    registration: HostRegistration,
    home_root: Path,
    workspace_root: Path | None,
    include_smoke: bool,
) -> HostInspection:
    """Inspect one registered host."""
    adapter = registration.adapter
    capability = registration.capability
    if _host_is_absent(adapter=adapter, home_root=home_root, workspace_root=workspace_root):
        skipped = InspectionCheck(
            host_id=capability.host_id,
            check_id="host_prompt_present",
            status=CHECK_SKIP,
            reason_code=REASON_OK,
            recommendation=f"Install Sopify for {capability.host_id} to enable host-local diagnostics.",
        )
        return HostInspection(
            registration=registration,
            host_prompt=skipped,
            payload=InspectionCheck(
                host_id=capability.host_id,
                check_id="payload_present",
                status=CHECK_SKIP,
                reason_code=REASON_OK,
                recommendation=f"Install Sopify for {capability.host_id} to provision the global payload.",
            ),
            payload_bundle=PayloadBundleResolution(
                source_kind=SOURCE_KIND_UNRESOLVED,
                reason_code="HOST_NOT_INSTALLED",
                status=CHECK_SKIP,
                recommendation=f"Install Sopify for {capability.host_id} to provision the global payload bundle index.",
            ),
            workspace_bundle=InspectionCheck(
                host_id=capability.host_id,
                check_id="workspace_bundle_manifest",
                status=CHECK_SKIP,
                reason_code=REASON_OK,
                recommendation=f"Install Sopify for {capability.host_id} before checking workspace bundle health.",
            ),
            handoff_first=InspectionCheck(
                host_id=capability.host_id,
                check_id="workspace_handoff_first",
                status=CHECK_SKIP,
                reason_code=REASON_OK,
            ),
            preferences_preload=InspectionCheck(
                host_id=capability.host_id,
                check_id="workspace_preferences_preload",
                status=CHECK_SKIP,
                reason_code=REASON_OK,
            ),
            smoke=InspectionCheck(
                host_id=capability.host_id,
                check_id="bundle_smoke",
                status=CHECK_SKIP,
                reason_code=REASON_OK,
            ),
        )
    host_prompt = _inspect_host_prompt(adapter=adapter, capability=capability, home_root=home_root, workspace_root=workspace_root)
    payload = _inspect_payload(adapter=adapter, capability=capability, home_root=home_root)
    payload_bundle = inspect_payload_bundle_resolution(payload_root=adapter.payload_root(home_root), host_id=capability.host_id)
    if workspace_root is None:
        workspace_bundle = InspectionCheck(
            host_id=capability.host_id,
            check_id="workspace_bundle_manifest",
            status=CHECK_SKIP,
            reason_code=REASON_WORKSPACE_NOT_REQUESTED,
            recommendation="Workspace bootstrap was not requested. Trigger Sopify in a project workspace to bootstrap on demand.",
        )
        handoff_first = InspectionCheck(
            host_id=capability.host_id,
            check_id="workspace_handoff_first",
            status=CHECK_SKIP,
            reason_code=REASON_WORKSPACE_NOT_REQUESTED,
            recommendation="Trigger Sopify in a project workspace to bootstrap on demand.",
        )
        preferences_preload = InspectionCheck(
            host_id=capability.host_id,
            check_id="workspace_preferences_preload",
            status=CHECK_SKIP,
            reason_code=REASON_WORKSPACE_NOT_REQUESTED,
            recommendation="Trigger Sopify in a project workspace to bootstrap on demand.",
        )
        smoke = _inspect_smoke(
            adapter=adapter,
            capability=capability,
            home_root=home_root,
            include_smoke=include_smoke,
        )
        return HostInspection(
            registration=registration,
            host_prompt=host_prompt,
            payload=payload,
            payload_bundle=payload_bundle,
            workspace_bundle=workspace_bundle,
            handoff_first=handoff_first,
            preferences_preload=preferences_preload,
            smoke=smoke,
        )
    workspace_bundle = _inspect_workspace_bundle(
        adapter=adapter,
        capability=capability,
        home_root=home_root,
        workspace_root=workspace_root,
    )
    capability_manifest = _resolve_workspace_capability_manifest(
        adapter=adapter,
        home_root=home_root,
        workspace_root=workspace_root,
        workspace_bundle=workspace_bundle,
    )
    handoff_first = _inspect_workspace_capability(
        capability=capability,
        workspace_bundle=workspace_bundle,
        capability_manifest=capability_manifest,
        check_id="workspace_handoff_first",
        manifest_key="writes_handoff_file",
        recommendation="Refresh the workspace bundle so handoff-first runtime contracts stay available.",
    )
    preferences_preload = _inspect_workspace_capability(
        capability=capability,
        workspace_bundle=workspace_bundle,
        capability_manifest=capability_manifest,
        check_id="workspace_preferences_preload",
        manifest_key="preferences_preload",
        recommendation="Refresh the workspace bundle so preferences preload stays available.",
    )
    smoke = _inspect_smoke(
        adapter=adapter,
        capability=capability,
        home_root=home_root,
        include_smoke=include_smoke,
    )
    return HostInspection(
        registration=registration,
        host_prompt=host_prompt,
        payload=payload,
        payload_bundle=payload_bundle,
        workspace_bundle=workspace_bundle,
        handoff_first=handoff_first,
        preferences_preload=preferences_preload,
        smoke=smoke,
    )


def inspect_workspace_state(workspace_root: Path | None) -> dict[str, object]:
    """Return a lightweight view of current workspace protocol state."""
    if workspace_root is None:
        return {
            "requested": False,
            "root": None,
            "bootstrap_mode": "on_first_project_trigger",
            "sopify_skills_present": None,
            "active_plan": None,
            "pending_checkpoint": None,
        }
    state_root = workspace_root / ".sopify-skills" / "state"
    active_plan_json = _read_json(state_root / "active_plan.json")
    current_handoff_json = _read_json(state_root / "current_handoff.json")
    return {
        "requested": True,
        "root": str(workspace_root),
        "bootstrap_mode": "prewarmed",
        "sopify_skills_present": (workspace_root / ".sopify-skills").is_dir(),
        "active_plan": str(active_plan_json.get("plan_id") or "") or None,
        "pending_checkpoint": current_handoff_json.get("required_host_action"),
    }


def build_status_payload(*, home_root: Path, workspace_root: Path | None) -> dict[str, object]:
    """Build the machine contract for `sopify status`."""
    inspections = inspect_all_hosts(home_root=home_root, workspace_root=workspace_root, include_smoke=False)
    hosts = [inspection.to_status_dict() for inspection in inspections]
    return {
        "schema_version": STATUS_SCHEMA_VERSION,
        "hosts": hosts,
        "state": _build_status_summary(hosts),
        "workspace_state": inspect_workspace_state(workspace_root),
    }


def build_doctor_payload(*, home_root: Path, workspace_root: Path | None) -> dict[str, object]:
    """Build the machine contract for `sopify doctor`."""
    inspections = inspect_all_hosts(home_root=home_root, workspace_root=workspace_root, include_smoke=True)
    checks = [check.to_dict() for inspection in inspections for check in inspection.doctor_checks()]
    workspace_state = inspect_workspace_state(workspace_root)
    checks.extend(check.to_dict() for check in _protocol_state_checks(workspace_state))
    return {
        "schema_version": DOCTOR_SCHEMA_VERSION,
        "checks": checks,
        "summary": _build_doctor_summary(checks),
    }


def render_status_text(payload: dict[str, object]) -> str:
    """Render a concise text summary for `sopify status`."""
    lines = [
        "Sopify status:",
        f"  overall: {payload['state']['overall_status']}",
        "Hosts:",
    ]
    for host in payload["hosts"]:
        state = host["state"]
        # Workspace-scope hosts: compact line without payload/bundle noise
        if state.get("workspace_bundle_healthy") == STATUS_NOT_APPLICABLE:
            lines.append(
                "  - {host_id}: tier={support_tier}, installed={installed}, configured={configured}".format(
                    host_id=host["host_id"],
                    support_tier=host["support_tier"],
                    installed=state["installed"],
                    configured=state["configured"],
                )
            )
            continue
        payload_bundle = host.get("payload_bundle") or {}
        workspace_bundle = host.get("workspace_bundle") or {}
        lines.append(
            "  - {host_id}: tier={support_tier}, installed={installed}, configured={configured}, workspace_bundle_healthy={workspace_bundle_healthy}, payload_bundle={payload_source_kind} ({payload_reason_code})".format(
                host_id=host["host_id"],
                support_tier=host["support_tier"],
                installed=state["installed"],
                configured=state["configured"],
                workspace_bundle_healthy=state["workspace_bundle_healthy"],
                payload_source_kind=payload_bundle.get("source_kind", SOURCE_KIND_UNRESOLVED),
                payload_reason_code=payload_bundle.get("reason_code", REASON_GLOBAL_INDEX_CORRUPTED),
            )
        )
        workspace_summary = render_outcome_summary(workspace_bundle)
        if workspace_summary:
            lines.append(f"    workspace_outcome: {workspace_summary}")
        payload_summary = render_outcome_summary(payload_bundle)
        if payload_summary:
            lines.append(f"    payload_outcome: {payload_summary}")
        warning_identifiers = diagnostic_identifiers_from_evidence(workspace_bundle.get("evidence") or ())
        if warning_identifiers:
            lines.append(f"    workspace_warning: {', '.join(warning_identifiers)}")
        if payload_bundle.get("recommendation"):
            lines.append(f"    payload_hint: {payload_bundle['recommendation']}")
    workspace_state = payload["workspace_state"]
    lines.append("Workspace:")
    if not workspace_state["requested"]:
        lines.extend(
            [
                "  requested: no",
                "  bootstrap_mode: on_first_project_trigger",
                "  state: will bootstrap on first project trigger",
            ]
        )
    else:
        lines.extend(
            [
                "  requested: yes",
                f"  root: {workspace_state['root']}",
                f"  sopify_skills_present: {workspace_state['sopify_skills_present']}",
                f"  active_plan: {workspace_state['active_plan'] or '(none)'}",
                f"  pending_checkpoint: {_CHECKPOINT_LABELS.get(workspace_state['pending_checkpoint'], workspace_state['pending_checkpoint']) if workspace_state['pending_checkpoint'] else '(none)'}",
            ]
        )
    return "\n".join(lines)


def render_doctor_text(payload: dict[str, object]) -> str:
    """Render a concise text summary for `sopify doctor`."""
    lines = [
        "Sopify doctor:",
        f"  overall_status: {payload['summary']['overall_status']}",
        f"  pass: {payload['summary']['pass_count']}",
        f"  warn: {payload['summary']['warn_count']}",
        f"  fail: {payload['summary']['fail_count']}",
        f"  skip: {payload['summary']['skip_count']}",
        "Checks:",
    ]
    for check in payload["checks"]:
        prefix = f"{check.get('host_id')}:" if check.get("host_id") else ""
        source_suffix = f" [{check['source_kind']}]" if check.get("source_kind") else ""
        line = f"  - {prefix}{check['check_id']} -> {check['status']} ({check['reason_code']}){source_suffix}"
        outcome_summary = render_outcome_summary(check)
        if outcome_summary:
            line += f" | outcome: {outcome_summary}"
        if check.get("recommendation"):
            line += f" | {check['recommendation']}"
        display_evidence = _displayable_evidence(check.get("evidence") or ())
        if display_evidence:
            line += f" | evidence: {', '.join(display_evidence)}"
        lines.append(line)
        for detail in _render_structured_evidence_lines(check.get("evidence")):
            lines.append(f"    {detail}")
    return "\n".join(lines)


def _render_structured_evidence_lines(evidence: object) -> tuple[str, ...]:
    if not isinstance(evidence, Mapping):
        return ()
    violations = evidence.get("violations")
    if not isinstance(violations, list):
        return ()
    rendered: list[str] = []
    for item in violations:
        if not isinstance(item, Mapping):
            continue
        field_name = str(item.get("field") or "unknown")
        error_kind = str(item.get("error_kind") or "invalid_value")
        actual_kind = str(item.get("actual_kind") or "").strip()
        detail = str(item.get("detail") or "").strip()
        message = f"{field_name}: {error_kind}"
        if actual_kind:
            message += f" ({actual_kind})"
        if detail:
            message += f" - {detail}"
        rendered.append(message)
    return tuple(rendered)


def _protocol_state_checks(workspace_state: dict[str, object]) -> tuple[InspectionCheck, ...]:
    if not workspace_state.get("requested"):
        return ()
    if not workspace_state.get("sopify_skills_present"):
        return (
            InspectionCheck(
                check_id="workspace_protocol_state",
                status=CHECK_WARN,
                reason_code="SOPIFY_SKILLS_MISSING",
                recommendation="Trigger Sopify in this workspace to bootstrap protocol state.",
            ),
        )
    checks: list[InspectionCheck] = []
    workspace_root = Path(str(workspace_state["root"]))
    state_root = workspace_root / ".sopify-skills" / "state"
    for filename, check_id in (
        ("active_plan.json", "active_plan_health"),
        ("current_handoff.json", "current_handoff_health"),
    ):
        file_path = state_root / filename
        if not file_path.is_file():
            checks.append(InspectionCheck(
                check_id=check_id,
                status=CHECK_WARN,
                reason_code="STATE_FILE_MISSING",
                evidence=(str(file_path),),
            ))
            continue
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            checks.append(InspectionCheck(
                check_id=check_id,
                status=CHECK_WARN,
                reason_code="STATE_FILE_INVALID",
                evidence=(str(file_path),),
            ))
            continue
        if not isinstance(payload, dict):
            checks.append(InspectionCheck(
                check_id=check_id,
                status=CHECK_WARN,
                reason_code="STATE_FILE_INVALID",
                evidence=(str(file_path),),
            ))
    return tuple(checks)




def _inspect_host_prompt(*, adapter: HostAdapter, capability: HostCapability, home_root: Path, workspace_root: Path | None = None) -> InspectionCheck:
    try:
        if adapter.is_workspace_scope:
            if workspace_root is None:
                raise InstallError("Workspace-scope host requires --workspace for verification")
            paths = adapter.workspace_expected_paths(workspace_root)
            missing = [p for p in paths if not p.exists()]
            if missing:
                raise InstallError(f"Host install verification failed: {missing[0]}")
        else:
            paths = validate_host_install(adapter, home_root=home_root)
        return InspectionCheck(
            host_id=capability.host_id,
            check_id="host_prompt_present",
            status=CHECK_PASS,
            reason_code=REASON_OK,
            evidence=tuple(str(path) for path in paths),
        )
    except InstallError as exc:
        return InspectionCheck(
            host_id=capability.host_id,
            check_id="host_prompt_present",
            status=CHECK_FAIL,
            reason_code=_reason_code_from_install_error(exc),
            evidence=_paths_from_error(exc),
            recommendation=f"Run python3 scripts/install_sopify.py --target {capability.host_id}:zh-CN to install the host prompt layer.",
        )


def _inspect_payload(*, adapter: HostAdapter, capability: HostCapability, home_root: Path) -> InspectionCheck:
    payload_root = adapter.payload_root(home_root)
    try:
        paths = validate_payload_install(payload_root)
        return InspectionCheck(
            host_id=capability.host_id,
            check_id="payload_present",
            status=CHECK_PASS,
            reason_code=REASON_OK,
            evidence=tuple(str(path) for path in paths),
        )
    except InstallError as exc:
        return InspectionCheck(
            host_id=capability.host_id,
            check_id="payload_present",
            status=CHECK_FAIL,
            reason_code=_reason_code_from_install_error(exc),
            evidence=_paths_from_error(exc),
            recommendation=f"Run python3 scripts/install_sopify.py --target {capability.host_id}:zh-CN to refresh the host payload.",
        )


def inspect_payload_bundle_resolution(*, payload_root: Path, host_id: str, bundle_version: str | None = None) -> PayloadBundleResolution:
    payload_manifest_path = payload_root / "payload-manifest.json"
    if not payload_manifest_path.is_file():
        return PayloadBundleResolution(
            source_kind=SOURCE_KIND_UNRESOLVED,
            reason_code=REASON_GLOBAL_BUNDLE_MISSING,
            status=CHECK_FAIL,
            recommendation=_payload_bundle_recommendation(host_id, REASON_GLOBAL_BUNDLE_MISSING),
        )

    payload_manifest = _read_json(payload_manifest_path)
    if not payload_manifest:
        return PayloadBundleResolution(
            source_kind=SOURCE_KIND_UNRESOLVED,
            reason_code=REASON_GLOBAL_INDEX_CORRUPTED,
            status=CHECK_FAIL,
            recommendation=_payload_bundle_recommendation(host_id, REASON_GLOBAL_INDEX_CORRUPTED),
        )

    source_kind = SOURCE_KIND_GLOBAL_ACTIVE if str(payload_manifest.get("bundles_dir") or "").strip() else SOURCE_KIND_LEGACY_LAYOUT
    try:
        bundle_root = resolve_payload_bundle_root(payload_root, bundle_version=bundle_version)
    except InstallError:
        return PayloadBundleResolution(
            source_kind=source_kind,
            reason_code=REASON_GLOBAL_INDEX_CORRUPTED,
            status=CHECK_FAIL,
            recommendation=_payload_bundle_recommendation(host_id, REASON_GLOBAL_INDEX_CORRUPTED),
        )

    bundle_manifest_path = bundle_root / "manifest.json"
    if not bundle_manifest_path.is_file():
        return PayloadBundleResolution(
            source_kind=source_kind,
            reason_code=REASON_GLOBAL_BUNDLE_MISSING,
            status=CHECK_FAIL,
            bundle_root=bundle_root,
            bundle_manifest_path=bundle_manifest_path,
            recommendation=_payload_bundle_recommendation(host_id, REASON_GLOBAL_BUNDLE_MISSING),
        )

    try:
        validate_bundle_install(bundle_root)
    except InstallError:
        return PayloadBundleResolution(
            source_kind=source_kind,
            reason_code=REASON_GLOBAL_BUNDLE_INCOMPATIBLE,
            status=CHECK_FAIL,
            bundle_root=bundle_root,
            bundle_manifest_path=bundle_manifest_path,
            recommendation=_payload_bundle_recommendation(host_id, REASON_GLOBAL_BUNDLE_INCOMPATIBLE),
        )

    ready_reason = REASON_PAYLOAD_BUNDLE_READY
    ready_status = CHECK_PASS
    recommendation = None
    return PayloadBundleResolution(
        source_kind=source_kind,
        reason_code=ready_reason,
        status=ready_status,
        bundle_root=bundle_root,
        bundle_manifest_path=bundle_manifest_path,
        recommendation=recommendation,
    )


def _inspect_workspace_bundle(
    *,
    adapter: HostAdapter,
    capability: HostCapability,
    home_root: Path,
    workspace_root: Path,
) -> InspectionCheck:
    payload_root = adapter.payload_root(home_root)
    bundle_root = workspace_root / ".sopify-skills"
    try:
        current_manifest_path, current_manifest = validate_workspace_stub_manifest(bundle_root)
    except InstallError as exc:
        current_manifest_path = bundle_root / "sopify.json"
        reason_code = "MISSING_BUNDLE" if not current_manifest_path.exists() else REASON_STUB_INVALID
        return InspectionCheck(
            host_id=capability.host_id,
            check_id="workspace_bundle_manifest",
            status=CHECK_FAIL,
            reason_code=reason_code,
            evidence=tuple(str(path) for path in (current_manifest_path, bundle_root) if path.exists()),
            recommendation=_workspace_bundle_recommendation(
                capability.host_id,
                workspace_root,
                reason_code,
                str(exc),
            ),
        )

    selected_bundle_version = current_manifest.get("bundle_version")
    selected_bundle_root: Path | None = None
    bundle_manifest_path: Path | None = None
    bundle_manifest: dict[str, Any] = {}
    global_reason_code: str | None = None
    global_message: str | None = None
    try:
        _payload_manifest_path, payload_manifest, bundle_manifest_path, bundle_manifest = validate_payload_manifests(
            payload_root,
            bundle_version=selected_bundle_version,
        )
        selected_bundle_root = bundle_manifest_path.parent
    except InstallError:
        payload_manifest = _read_json(payload_root / "payload-manifest.json")
        if payload_manifest:
            try:
                (
                    selected_bundle_root,
                    bundle_manifest_path,
                    bundle_manifest,
                    global_reason_code,
                    global_message,
                ) = _resolve_selected_payload_bundle(
                    payload_root=payload_root,
                    payload_manifest=payload_manifest,
                    current_manifest=current_manifest,
                )
            except ValueError:
                payload_manifest = {}
        if not payload_manifest or (not bundle_manifest and bundle_manifest_path is None):
            resolution = inspect_payload_bundle_resolution(
                payload_root=payload_root,
                host_id=capability.host_id,
                bundle_version=selected_bundle_version,
            )
            evidence = tuple(
                str(path)
                for path in (current_manifest_path, resolution.bundle_manifest_path, resolution.bundle_root)
                if path is not None and path.exists()
            )
            return InspectionCheck(
                host_id=capability.host_id,
                check_id="workspace_bundle_manifest",
                status=CHECK_FAIL,
                reason_code=resolution.reason_code,
                evidence=evidence,
                recommendation=_workspace_bundle_recommendation(
                    capability.host_id,
                    workspace_root,
                    resolution.reason_code,
                    resolution.recommendation or "Selected global bundle is unavailable.",
                ),
            )

    state, reason_code, message, _from_version = _classify_workspace_bundle(
        current_manifest=current_manifest,
        payload_manifest=payload_manifest,
        bundle_manifest=bundle_manifest,
        current_manifest_path=current_manifest_path,
        bundle_root=bundle_root,
        global_bundle_root=selected_bundle_root,
        global_reason_code=global_reason_code,
        global_message=global_message,
    )
    status = CHECK_FAIL
    if state in STATUS_READY_STATES:
        status = CHECK_PASS
    elif state in STATUS_WARN_STATES:
        status = CHECK_WARN
    evidence = tuple(
        str(path)
        for path in (current_manifest_path, bundle_root)
        if path.exists()
    )
    evidence += _workspace_bundle_evidence(
        workspace_root=workspace_root,
        current_manifest=current_manifest,
        reason_code=reason_code,
    )
    return InspectionCheck(
        host_id=capability.host_id,
        check_id="workspace_bundle_manifest",
        status=status,
        reason_code=reason_code,
        evidence=evidence,
        recommendation=_workspace_bundle_recommendation(capability.host_id, workspace_root, reason_code, message),
    )


def _inspect_workspace_capability(
    *,
    capability: HostCapability,
    workspace_bundle: InspectionCheck,
    capability_manifest: dict[str, Any],
    check_id: str,
    manifest_key: str,
    recommendation: str,
) -> InspectionCheck:
    if workspace_bundle.status != CHECK_PASS:
        return InspectionCheck(
            host_id=capability.host_id,
            check_id=check_id,
            status=workspace_bundle.status,
            reason_code=workspace_bundle.reason_code,
            evidence=workspace_bundle.evidence,
            recommendation=recommendation,
        )
    current_capabilities = capability_manifest.get("capabilities") or {}
    if current_capabilities.get(manifest_key):
        return InspectionCheck(
            host_id=capability.host_id,
            check_id=check_id,
            status=CHECK_PASS,
            reason_code=REASON_OK,
        )
    return InspectionCheck(
        host_id=capability.host_id,
        check_id=check_id,
        status=CHECK_FAIL,
        reason_code="MISSING_REQUIRED_CAPABILITY",
        recommendation=recommendation,
    )


def _resolve_workspace_capability_manifest(
    *,
    adapter: HostAdapter,
    home_root: Path,
    workspace_root: Path,
    workspace_bundle: InspectionCheck,
) -> dict[str, Any]:
    if workspace_bundle.status != CHECK_PASS:
        return {}

    bundle_root = workspace_root / ".sopify-skills"
    try:
        _manifest_path, current_manifest = validate_workspace_stub_manifest(bundle_root)
        selected_bundle_version = current_manifest.get("bundle_version")
        _payload_manifest_path, _payload_manifest, _bundle_manifest_path, capability_manifest = validate_payload_manifests(
            adapter.payload_root(home_root),
            bundle_version=selected_bundle_version,
        )
    except InstallError:
        return {}
    return capability_manifest


def _inspect_smoke(
    *,
    adapter: HostAdapter,
    capability: HostCapability,
    home_root: Path,
    include_smoke: bool,
) -> InspectionCheck:
    if not include_smoke:
        return InspectionCheck(
            host_id=capability.host_id,
            check_id="bundle_smoke",
            status=CHECK_SKIP,
            reason_code=REASON_OK,
        )

    try:
        bundle_root = resolve_payload_bundle_root(adapter.payload_root(home_root))
        stdout = run_bundle_smoke_check(
            bundle_root,
            payload_manifest_path=adapter.payload_root(home_root) / "payload-manifest.json",
        )
        evidence = (stdout.splitlines()[0],) if stdout else ()
        return InspectionCheck(
            host_id=capability.host_id,
            check_id="bundle_smoke",
            status=CHECK_PASS,
            reason_code=REASON_OK,
            evidence=evidence,
        )
    except InstallError as exc:
        return InspectionCheck(
            host_id=capability.host_id,
            check_id="bundle_smoke",
            status=CHECK_FAIL,
            reason_code=_reason_code_from_install_error(exc, default="UNEXPECTED_ERROR"),
            evidence=_paths_from_error(exc),
            recommendation=f"Refresh the {capability.host_id} payload bundle and rerun the bundled smoke check.",
        )


def _build_status_summary(hosts: list[dict[str, object]]) -> dict[str, object]:
    installed_hosts = [host["host_id"] for host in hosts if host["state"]["installed"] == STATUS_YES]
    configured_hosts = [host["host_id"] for host in hosts if host["state"]["configured"] == STATUS_YES]
    workspace_bundle_healthy_hosts = [
        host["host_id"] for host in hosts if host["state"]["workspace_bundle_healthy"] == STATUS_YES
    ]
    installable_hosts = [host["host_id"] for host in hosts if host["install_enabled"]]
    overall_status = "missing"
    if workspace_bundle_healthy_hosts:
        overall_status = "ready"
    elif installed_hosts or configured_hosts:
        overall_status = "partial"
    return {
        "overall_status": overall_status,
        "installable_hosts": installable_hosts,
        "installed_hosts": installed_hosts,
        "configured_hosts": configured_hosts,
        "workspace_bundle_healthy_hosts": workspace_bundle_healthy_hosts,
    }


def _build_doctor_summary(checks: list[dict[str, object]]) -> dict[str, object]:
    pass_count = sum(1 for check in checks if check["status"] == CHECK_PASS)
    warn_count = sum(1 for check in checks if check["status"] == CHECK_WARN)
    fail_count = sum(1 for check in checks if check["status"] == CHECK_FAIL)
    skip_count = sum(1 for check in checks if check["status"] == CHECK_SKIP)
    overall_status = CHECK_PASS
    if fail_count:
        overall_status = CHECK_FAIL
    elif warn_count:
        overall_status = CHECK_WARN
    elif skip_count and not pass_count:
        overall_status = CHECK_SKIP
    return {
        "overall_status": overall_status,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "skip_count": skip_count,
    }


def _workspace_bundle_recommendation(host_id: str, workspace_root: Path, reason_code: str, message: str) -> str | None:
    if reason_code in {"MISSING_BUNDLE", "WORKSPACE_BUNDLE_OUTDATED"}:
        return f"Sopify is not enabled in {workspace_root} yet. Trigger Sopify there to bootstrap on demand."
    if reason_code == REASON_STUB_INVALID:
        return (
            f"The local `.sopify-skills/sopify.json` in {workspace_root} looks invalid. "
            f"Rerun Sopify bootstrap, or delete that file and retry."
        )
    if reason_code == REASON_STUB_SELECTED:
        return None
    if reason_code in {
        REASON_GLOBAL_BUNDLE_MISSING,
        REASON_GLOBAL_BUNDLE_INCOMPATIBLE,
        REASON_GLOBAL_INDEX_CORRUPTED,
    }:
        # For GLOBAL_BUNDLE_MISSING, prefer `message` which may carry
        # stale-stub diagnostic from _stale_stub_diagnostic(); fall back
        # to generic _payload_bundle_recommendation for other codes or
        # when message is empty.
        if reason_code == REASON_GLOBAL_BUNDLE_MISSING and message:
            return message
        return _payload_bundle_recommendation(host_id, reason_code) or message
    return message



def _workspace_bundle_evidence(
    *,
    workspace_root: Path,
    current_manifest: dict[str, Any],
    reason_code: str,
) -> tuple[str, ...]:
    evidence: list[str] = []
    ignore_mode = str(current_manifest.get("ignore_mode") or "").strip()
    if ignore_mode == "noop" and not (workspace_root / ".git").exists():
        evidence.extend((DIAGNOSTIC_NON_GIT_WORKSPACE, "ignore_mode=noop"))
    elif reason_code == REASON_STUB_SELECTED and ignore_mode:
        evidence.append(f"ignore_mode={ignore_mode}")
    return tuple(item for item in evidence if item)


def _displayable_evidence(evidence: object) -> tuple[str, ...]:
    values: list[str] = []
    for item in evidence if isinstance(evidence, (list, tuple)) else ():
        normalized = str(item or "").strip()
        if not normalized or normalized.startswith("/"):
            continue
        values.append(normalized)
    return tuple(values[:3])


def _check_state_value(check: InspectionCheck) -> str:
    if check.reason_code == REASON_WORKSPACE_NOT_REQUESTED:
        return STATUS_NOT_REQUESTED
    if check.status == CHECK_PASS:
        return STATUS_YES
    return STATUS_NO


def _reason_code_from_install_error(exc: InstallError, *, default: str = "MISSING_REQUIRED_FILE") -> str:
    message = str(exc)
    if "schema" in message.lower():
        return "SCHEMA_VERSION_MISMATCH"
    if "capabilit" in message.lower():
        return "MISSING_REQUIRED_CAPABILITY"
    if "missing" in message.lower() or "verification failed" in message.lower():
        return "MISSING_REQUIRED_FILE"
    return default



def _payload_bundle_recommendation(host_id: str, reason_code: str) -> str | None:
    refresh_command = f"python3 scripts/install_sopify.py --target {host_id}:zh-CN"
    if reason_code == REASON_GLOBAL_BUNDLE_MISSING:
        return f"Refresh the {host_id} payload because the selected global bundle is missing: {refresh_command}"
    if reason_code == REASON_GLOBAL_BUNDLE_INCOMPATIBLE:
        return f"Refresh the {host_id} payload because the selected global bundle is incomplete or incompatible: {refresh_command}"
    if reason_code == REASON_GLOBAL_INDEX_CORRUPTED:
        return f"Refresh the {host_id} payload because the bundle index is invalid or inconsistent: {refresh_command}"
    return None


def _paths_from_error(exc: InstallError) -> tuple[str, ...]:
    message = str(exc)
    if "[" in message and "]" in message:
        start = message.find("[")
        end = message.rfind("]")
        if start >= 0 and end > start:
            return tuple(part.strip(" []'") for part in message[start + 1 : end].split(",") if part.strip(" []'"))
    if ":" in message:
        candidate = message.rsplit(":", 1)[-1].strip()
        if candidate.startswith("/"):
            return (candidate,)
    return ()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload



def _payload_evidence_paths(payload_root: Path) -> tuple[Path, ...]:
    payload_manifest_path = payload_root / "payload-manifest.json"
    evidence: list[Path] = []
    if payload_manifest_path.exists():
        evidence.append(payload_manifest_path)
        payload_manifest = _read_json(payload_manifest_path)
        if payload_manifest:
            try:
                evidence.append(resolve_payload_bundle_root(payload_root).resolve() / "manifest.json")
            except InstallError:
                bundle_manifest = str(payload_manifest.get("bundle_manifest") or "").strip()
                if bundle_manifest:
                    candidate = payload_root / bundle_manifest
                    if candidate.exists():
                        evidence.append(candidate)
    return tuple(evidence)


def _host_is_absent(*, adapter: HostAdapter, home_root: Path, workspace_root: Path | None = None) -> bool:
    if adapter.is_workspace_scope:
        # Workspace-scope hosts are checked against workspace, not HOME
        if workspace_root is None:
            return True
        return not any(p.exists() for p in adapter.workspace_expected_paths(workspace_root))
    return not adapter.destination_root(home_root).exists() and not adapter.payload_root(home_root).exists()
