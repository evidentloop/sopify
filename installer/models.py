"""Shared installer models and target parsing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

LANGUAGE_DIRECTORY_MAP = {
    "zh-CN": "CN",
    "en-US": "EN",
}

SUPPORTED_HOSTS = {"codex", "claude"}


class InstallError(RuntimeError):
    """Raised when the installer cannot complete safely."""


@dataclass(frozen=True)
class InstallTarget:
    """Normalized installer target."""

    host: str
    language: str

    @property
    def value(self) -> str:
        return f"{self.host}:{self.language}"

    @property
    def language_directory(self) -> str:
        return LANGUAGE_DIRECTORY_MAP[self.language]


@dataclass(frozen=True)
class InstallResult:
    """Summary of a completed Sopify installation."""

    target: InstallTarget
    workspace_root: Path | None
    host_root: Path
    payload_root: Path
    bundle_root: Path | None
    host_install: "InstallPhaseResult"
    payload_install: "InstallPhaseResult"
    workspace_bootstrap: "BootstrapResult | None"
    smoke_output: str


@dataclass(frozen=True)
class InstallPhaseResult:
    """Result for one installer-owned phase such as host or payload setup."""

    action: str
    root: Path
    version: str | None
    paths: tuple[Path, ...]


@dataclass(frozen=True)
class BootstrapResult:
    """Structured result returned by the workspace bootstrap helper."""

    action: str
    state: str
    reason_code: str
    workspace_root: Path
    bundle_root: Path
    from_version: str | None
    to_version: str | None
    message: str

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "BootstrapResult":
        return cls(
            action=str(data.get("action") or "failed"),
            state=str(data.get("state") or "INCOMPATIBLE"),
            reason_code=str(data.get("reason_code") or "UNKNOWN"),
            workspace_root=Path(str(data.get("workspace_root") or ".")),
            bundle_root=Path(str(data.get("bundle_root") or ".")),
            from_version=_string_or_none(data.get("from_version")),
            to_version=_string_or_none(data.get("to_version")),
            message=str(data.get("message") or ""),
        )


def parse_install_target(raw_value: str) -> InstallTarget:
    """Parse a CLI target like `codex:zh-CN`."""
    value = raw_value.strip()
    host, separator, language = value.partition(":")
    if not separator:
        raise InstallError("Target must use the format <host:lang>, for example codex:zh-CN")
    if host not in SUPPORTED_HOSTS:
        raise InstallError(f"Unsupported host: {host}")
    if language not in LANGUAGE_DIRECTORY_MAP:
        raise InstallError(f"Unsupported language: {language}")
    return InstallTarget(host=host, language=language)


def _string_or_none(value: object) -> str | None:
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    return None
