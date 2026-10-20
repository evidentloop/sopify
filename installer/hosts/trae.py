"""Trae CLI Skill entry, without an unverified global rule file."""

from installer.models import EntryMode, FeatureId, HostCapability, SupportTier

from .base import HostAdapter, HostRegistration

TRAE_ADAPTER = HostAdapter(
    host_name="trae",
    destination_dirname=".trae",
    header_filename="skills/sopify/SKILL.md",
    config_dir="~/.trae",
    default_language="en-US",
    flat_skills=True,
    entry_skill_template="skills/trae-entry-skill.md.template",
)

TRAE_HOST = HostRegistration(
    adapter=TRAE_ADAPTER,
    capability=HostCapability(
        host_id="trae",
        support_tier=SupportTier.BASELINE_SUPPORTED,
        install_enabled=True,
        declared_features=(FeatureId.PROMPT_INSTALL, FeatureId.PAYLOAD_INSTALL),
        verified_features=(FeatureId.PROMPT_INSTALL, FeatureId.PAYLOAD_INSTALL),
        declared_enhancements=(),
        entry_modes=(EntryMode.PROMPT_ONLY,),
        doctor_checks=("host_prompt_present", "global_skill_tree_present",
                       "payload_present", "trae_cli_behavior"),
        smoke_targets=(),
    ),
)
