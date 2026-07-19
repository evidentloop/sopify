"""Codex host adapter."""

from __future__ import annotations

from installer.models import EntryMode, EnhancementGroup, FeatureId, HostCapability, SupportTier

from .base import HostAdapter, HostRegistration

CODEX_ADAPTER = HostAdapter(
    host_name="codex",
    destination_dirname=".codex",
    header_filename="AGENTS.md",
    config_dir="~/.codex",
    skills_cli_agent="codex",
    skill_install_dirname=".agents/skills",
)

CODEX_CAPABILITY = HostCapability(
    host_id="codex",
    support_tier=SupportTier.PROTOCOL_VERIFIED,
    install_enabled=True,
    declared_features=(
        FeatureId.PROMPT_INSTALL,
        FeatureId.PAYLOAD_INSTALL,
        FeatureId.WORKSPACE_BOOTSTRAP,
        FeatureId.HANDOFF_FIRST,
        FeatureId.HOST_BRIDGE,
    ),
    verified_features=(
        FeatureId.PROMPT_INSTALL,
        FeatureId.PAYLOAD_INSTALL,
        FeatureId.WORKSPACE_BOOTSTRAP,
        FeatureId.HANDOFF_FIRST,
        FeatureId.HOST_BRIDGE,
    ),
    declared_enhancements=(
        EnhancementGroup.CONTINUATION,
        EnhancementGroup.INTERACTION,
        EnhancementGroup.AUDIT,
    ),
    entry_modes=(EntryMode.PROMPT_ONLY,),
    doctor_checks=(
        "host_prompt_present",
        "payload_present",
        "workspace_bundle_manifest",
        "workspace_handoff_first",
    ),
    smoke_targets=(),
)

CODEX_HOST = HostRegistration(adapter=CODEX_ADAPTER, capability=CODEX_CAPABILITY)
