"""Antigravity CLI global rules and direct-child Skills."""

from installer.models import EntryMode, FeatureId, HostCapability, SupportTier

from .base import HostAdapter, HostRegistration

ANTIGRAVITY_ADAPTER = HostAdapter(
    host_name="antigravity",
    destination_dirname=".gemini/config",
    header_filename="AGENTS.md",
    config_dir="~/.gemini/config",
    default_language="en-US",
    flat_skills=True,
)

ANTIGRAVITY_HOST = HostRegistration(
    adapter=ANTIGRAVITY_ADAPTER,
    capability=HostCapability(
        host_id="antigravity",
        support_tier=SupportTier.BASELINE_SUPPORTED,
        install_enabled=True,
        declared_features=(FeatureId.PROMPT_INSTALL, FeatureId.PAYLOAD_INSTALL),
        verified_features=(FeatureId.PROMPT_INSTALL, FeatureId.PAYLOAD_INSTALL),
        declared_enhancements=(),
        entry_modes=(EntryMode.PROMPT_ONLY,),
        doctor_checks=("host_prompt_present", "global_skill_tree_present",
                       "payload_present", "antigravity_cli_behavior"),
        smoke_targets=(),
    ),
)
