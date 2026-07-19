"""Qoder host adapter (home-scope hybrid, PROTOCOL_VERIFIED)."""

from __future__ import annotations

from installer.models import EntryMode, EnhancementGroup, FeatureId, HostCapability, SupportTier

from .base import HostAdapter, HostRegistration

QODER_ADAPTER = HostAdapter(
    host_name="qoder",
    destination_dirname=".qoder",
    header_filename="AGENTS.md",
    config_dir="~/.qoder",
    default_language="zh-CN",
    skills_cli_agent="qoder",
    skill_install_dirname=".qoder/skills",
)

QODER_CAPABILITY = HostCapability(
    host_id="qoder",
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

QODER_HOST = HostRegistration(adapter=QODER_ADAPTER, capability=QODER_CAPABILITY)
