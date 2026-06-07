"""Claude host adapter."""

from __future__ import annotations

from installer.models import EntryMode, EnhancementGroup, FeatureId, HostCapability, SupportTier

from .base import HostAdapter, HostRegistration

CLAUDE_ADAPTER = HostAdapter(
    host_name="claude",
    destination_dirname=".claude",
    header_filename="CLAUDE.md",
    config_dir="~/.claude",
)

CLAUDE_CAPABILITY = HostCapability(
    host_id="claude",
    support_tier=SupportTier.DEEP_VERIFIED,
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

CLAUDE_HOST = HostRegistration(adapter=CLAUDE_ADAPTER, capability=CLAUDE_CAPABILITY)
