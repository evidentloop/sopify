"""Explicit, optional EvidentLoop companion installation."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Mapping

from installer.hosts.base import HostAdapter
from installer.models import EvidentLoopInstallResult, InstallError

EVIDENTLOOP_PACKAGE = "evidentloop"
EVIDENTLOOP_SKILL_SOURCE = "evidentloop/evidentloop"
SKILLS_CLI_PACKAGE = "skills@latest"

_SKILL_NAME = "evidentloop"
_SKILL_ENTRYPOINT = "SKILL.md"
_SKILLS_CLI_PROJECT_DIR = Path(".agents") / "skills"


@dataclass(frozen=True)
class EvidentLoopInstallPlan:
    adapter: HostAdapter
    home_root: Path
    skill_dir: Path
    uv_path: str | None
    npx_path: str | None
    install_cli: bool
    install_skill: bool
    package_version: str | None


def prepare_evidentloop_install(
    adapter: HostAdapter,
    *,
    home_root: Path,
    workspace_root: Path | None = None,
) -> EvidentLoopInstallPlan:
    """Validate existing components and discover only the installers still needed."""
    if adapter.skills_cli_agent is None or adapter.skill_install_dirname is None:
        raise InstallError(
            f"EvidentLoop companion install is not supported for host '{adapter.host_name}': "
            "missing Skill install mapping"
        )

    skill_dir = adapter.skill_install_path(
        home_root=home_root,
        workspace_root=workspace_root,
        skill_name=_SKILL_NAME,
    )
    skill_path_occupied = _path_is_occupied(skill_dir)
    if skill_path_occupied:
        _validate_skill(skill_dir)

    cli_executable: Path | None = None
    package_version: str | None = None
    discovered_cli = shutil.which(EVIDENTLOOP_PACKAGE)
    if discovered_cli is not None:
        cli_executable = Path(discovered_cli).expanduser().resolve()
        package_version = _validate_cli(cli_executable, home_root=home_root)

    uv_path = shutil.which("uv") if cli_executable is None else None
    npx_path = shutil.which("npx") if not skill_path_occupied else None
    missing: list[str] = []
    if cli_executable is None and uv_path is None:
        missing.append("uv")
    if not skill_path_occupied and npx_path is None:
        missing.append("npx")
    if not skill_path_occupied and shutil.which("git") is None:
        missing.append("git")
    if missing:
        raise InstallError(
            "EvidentLoop companion preflight failed: "
            f"missing required command(s): {', '.join(missing)}"
        )

    return EvidentLoopInstallPlan(
        adapter=adapter,
        home_root=home_root,
        skill_dir=skill_dir,
        uv_path=uv_path,
        npx_path=npx_path,
        install_cli=cli_executable is None,
        install_skill=not skill_path_occupied,
        package_version=package_version,
    )


def install_evidentloop_companion(
    plan: EvidentLoopInstallPlan,
) -> EvidentLoopInstallResult:
    """Install missing components using EvidentLoop's current official sources."""
    cli_action = "reused"
    skill_action = "reused"
    package_version = plan.package_version

    if plan.install_cli:
        if plan.uv_path is None:  # Defensive: prepare() owns prerequisite checks.
            raise InstallError("EvidentLoop CLI install requires uv")
        _run_command(
            [plan.uv_path, "tool", "install", EVIDENTLOOP_PACKAGE],
            env=_base_child_env(plan.home_root),
            label="EvidentLoop CLI install",
        )
        cli_executable = _uv_tool_executable(plan)
        package_version = _validate_cli(cli_executable, home_root=plan.home_root)
        _validate_cli_on_path(cli_executable)
        cli_action = "installed"

    if plan.install_skill:
        _install_skill(plan)
        skill_action = "installed"

    if package_version is None:  # Defensive: installed or reused CLI must be validated.
        raise InstallError("EvidentLoop CLI version could not be determined")
    return EvidentLoopInstallResult(
        cli_action=cli_action,
        skill_action=skill_action,
        package_version=package_version,
        skill_path=plan.skill_dir / _SKILL_ENTRYPOINT,
    )


def _install_skill(plan: EvidentLoopInstallPlan) -> None:
    if plan.npx_path is None:  # Defensive: prepare() owns prerequisite checks.
        raise InstallError("EvidentLoop Skill install requires npx")
    if _path_is_occupied(plan.skill_dir):
        raise InstallError(
            f"EvidentLoop Skill path changed after preflight: {plan.skill_dir}"
        )

    with tempfile.TemporaryDirectory(prefix="sopify-evidentloop-") as temp_dir:
        staging_root = Path(temp_dir)
        staging_home = staging_root / "home"
        staging_home.mkdir()
        env = _base_child_env(staging_home)
        env["DISABLE_TELEMETRY"] = "1"
        env["DO_NOT_TRACK"] = "1"
        argv = [
            plan.npx_path,
            "--yes",
            SKILLS_CLI_PACKAGE,
            "add",
            EVIDENTLOOP_SKILL_SOURCE,
            "--skill",
            _SKILL_NAME,
        ]

        if plan.adapter.is_workspace_scope:
            argv.extend(["-a", str(plan.adapter.skills_cli_agent), "-y", "--copy"])
            staged_skill = staging_root / _SKILLS_CLI_PROJECT_DIR / _SKILL_NAME
        else:
            argv.extend(
                ["-g", "-a", str(plan.adapter.skills_cli_agent), "-y", "--copy"]
            )
            staged_skill = (
                staging_home / str(plan.adapter.skill_install_dirname) / _SKILL_NAME
            )

        _run_command(
            argv,
            env=env,
            label="EvidentLoop Skill install",
            cwd=staging_root,
        )
        _validate_skill(staged_skill)
        _copy_skill_directory(staged_skill, plan.skill_dir)

    _validate_skill(plan.skill_dir)


def _copy_skill_directory(source: Path, destination: Path) -> None:
    if _path_is_occupied(destination):
        raise InstallError(
            f"EvidentLoop Skill path changed during installation: {destination}"
        )
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=".evidentloop-copy-",
            dir=destination.parent,
        ) as temp_dir:
            staged_copy = Path(temp_dir) / destination.name
            shutil.copytree(source, staged_copy)
            staged_copy.replace(destination)
    except OSError as exc:
        raise InstallError(
            f"EvidentLoop Skill could not be copied to {destination}"
        ) from exc


def _validate_cli(executable: Path, *, home_root: Path) -> str:
    if not executable.is_absolute():
        raise InstallError("Existing EvidentLoop CLI path is not absolute")
    doctor = _run_command(
        [str(executable), "doctor", "--json"],
        env=_isolated_python_env(home_root),
        label="EvidentLoop CLI doctor",
    )
    payload = _json_object(doctor.stdout, label="EvidentLoop CLI doctor")
    if payload.get("status") not in {"ok", "warning"}:
        raise InstallError("EvidentLoop CLI doctor reported an unhealthy installation")
    package_version = payload.get("version")
    if not isinstance(package_version, str) or not package_version.strip():
        raise InstallError("EvidentLoop CLI doctor did not return a version")
    return package_version.strip()


def _validate_skill(skill_dir: Path) -> None:
    entrypoint = skill_dir / _SKILL_ENTRYPOINT
    if not skill_dir.is_dir() or not entrypoint.is_file():
        raise InstallError(
            f"EvidentLoop Skill directory is incomplete: expected {entrypoint}"
        )
    try:
        content = entrypoint.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise InstallError(f"EvidentLoop Skill is unreadable: {entrypoint}") from exc
    if not content.strip():
        raise InstallError(f"EvidentLoop Skill entrypoint is empty: {entrypoint}")

    lines = content.splitlines()
    names: list[str] = []
    frontmatter_closed = False
    if lines and lines[0].strip() == "---":
        for line in lines[1:]:
            if line.strip() == "---":
                frontmatter_closed = True
                break
            if line[:1].isspace():
                continue
            key, separator, value = line.partition(":")
            if separator and key.strip() == "name":
                name = value.strip()
                if len(name) >= 2 and name[0] == name[-1] and name[0] in "'\"":
                    name = name[1:-1]
                names.append(name)
    if not frontmatter_closed or names != [_SKILL_NAME]:
        raise InstallError(
            "EvidentLoop Skill identity is invalid: expected front matter "
            f"`name: {_SKILL_NAME}` in {entrypoint}"
        )


def _path_is_occupied(path: Path) -> bool:
    """Treat broken symlinks as existing so installation never overwrites them."""
    return path.exists() or path.is_symlink()


def _uv_tool_executable(plan: EvidentLoopInstallPlan) -> Path:
    if plan.uv_path is None:
        raise InstallError("uv executable is unavailable")
    completed = _run_command(
        [plan.uv_path, "tool", "dir", "--bin"],
        env=_base_child_env(plan.home_root),
        label="uv tool binary directory probe",
    )
    bin_dir = Path(completed.stdout.strip()).expanduser()
    if not bin_dir.is_absolute():
        raise InstallError("uv did not return an absolute tool binary directory")
    executable = bin_dir / ("evidentloop.exe" if os.name == "nt" else "evidentloop")
    if not executable.is_file():
        raise InstallError(f"EvidentLoop CLI is missing after install: {executable}")
    return executable.resolve()


def _validate_cli_on_path(executable: Path) -> None:
    discovered = shutil.which(EVIDENTLOOP_PACKAGE)
    if discovered is None:
        raise InstallError(
            "EvidentLoop CLI was installed and validated at "
            f"{executable}, but it is not discoverable on PATH. "
            f"Add {executable.parent} to PATH (for uv, run `uv tool update-shell`), "
            "restart the shell and AI host, then rerun the same install command"
        )
    discovered_path = Path(discovered).expanduser().resolve()
    if discovered_path != executable:
        raise InstallError(
            "EvidentLoop CLI was installed and validated at "
            f"{executable}, but PATH resolves `evidentloop` to {discovered_path}. "
            "Fix PATH precedence, restart the shell and AI host, then rerun the same "
            "install command"
        )


def _run_command(
    argv: list[str],
    *,
    env: Mapping[str, str],
    label: str,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            check=False,
            env=dict(env),
            cwd=str(cwd) if cwd is not None else None,
        )
    except OSError as exc:
        raise InstallError(f"{label} could not start") from exc
    if completed.returncode != 0:
        raise InstallError(f"{label} failed with exit code {completed.returncode}")
    return completed


def _json_object(raw_value: str, *, label: str) -> dict[str, object]:
    try:
        payload = json.loads(raw_value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise InstallError(f"{label} did not return valid JSON") from exc
    if not isinstance(payload, dict):
        raise InstallError(f"{label} did not return a JSON object")
    return payload


def _base_child_env(home_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(home_root)
    if os.name == "nt":
        env["USERPROFILE"] = str(home_root)
    return env


def _isolated_python_env(home_root: Path) -> dict[str, str]:
    env = _base_child_env(home_root)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["PYTHONNOUSERSITE"] = "1"
    return env
