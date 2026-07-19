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

EVIDENTLOOP_PACKAGE_VERSION = "0.1.0a2"
EVIDENTLOOP_SCHEMA_VERSION = "0.4"
EVIDENTLOOP_PROMPT_VERSION = "v0.5"
EVIDENTLOOP_SKILL_TAG = "v0.1.0a2"
EVIDENTLOOP_SKILL_COMMIT = "fcefb77083d32b034e56b04dcd085dcf5a835550"
EVIDENTLOOP_SKILL_REPOSITORY = "https://github.com/evidentloop/evidentloop.git"
SKILLS_CLI_VERSION = "1.5.9"

_SKILL_NAME = "evidentloop"
_SKILL_ENTRYPOINT = "SKILL.md"
_SKILL_REQUIRED_REFERENCE = Path("references") / "codex-cli-isolation.md"
_SKILLS_CLI_PROJECT_DIR = Path(".agents") / "skills"
_REQUIRED_SUBCOMMANDS = ("prepare", "finalize", "render", "revise")
_OFFICIAL_INSTALL_GUIDE = "https://github.com/evidentloop/evidentloop#quick-start"

_COMPATIBILITY_CODE = (
    "import json; import evidentloop; "
    "from evidentloop.api import finalize_review, prepare_local_diff, "
    "recover_interrupted_revision, render_audit_file, revise_audit; "
    "from evidentloop.review.core.prompt import PRODUCT_REVIEWER_PROMPT_VERSION; "
    "from evidentloop.validation import SCHEMA_VERSION; "
    "print(json.dumps({'package_version': evidentloop.__version__, "
    "'schema_version': SCHEMA_VERSION, "
    "'prompt_version': PRODUCT_REVIEWER_PROMPT_VERSION}))"
)


@dataclass(frozen=True)
class EvidentLoopInstallPlan:
    adapter: HostAdapter
    home_root: Path
    skill_dir: Path
    uv_path: str | None
    npx_path: str | None
    git_path: str | None
    install_cli: bool
    install_skill: bool


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
    discovered_cli = shutil.which("evidentloop")
    if discovered_cli is not None:
        cli_executable = Path(discovered_cli).expanduser().resolve()
        _validate_cli(cli_executable, home_root=home_root)

    uv_path = shutil.which("uv") if cli_executable is None else None
    npx_path = shutil.which("npx") if not skill_path_occupied else None
    git_path = shutil.which("git") if not skill_path_occupied else None
    missing: list[str] = []
    if cli_executable is None and uv_path is None:
        missing.append("uv")
    if not skill_path_occupied and npx_path is None:
        missing.append("npx")
    if not skill_path_occupied and git_path is None:
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
        git_path=git_path,
        install_cli=cli_executable is None,
        install_skill=not skill_path_occupied,
    )


def install_evidentloop_companion(
    plan: EvidentLoopInstallPlan,
) -> EvidentLoopInstallResult:
    """Install missing components and re-run the compatibility probes."""
    cli_action = "reused"
    skill_action = "reused"
    completed: list[str] = []

    try:
        if plan.install_cli:
            if plan.uv_path is None:  # Defensive: prepare() owns prerequisite checks.
                raise InstallError("EvidentLoop CLI install requires uv")
            _run_command(
                [
                    plan.uv_path,
                    "tool",
                    "install",
                    f"evidentloop=={EVIDENTLOOP_PACKAGE_VERSION}",
                ],
                env=_base_child_env(plan.home_root),
                label="EvidentLoop CLI install",
            )
            completed.append("CLI installed")
            cli_executable = _uv_tool_executable(plan)
            _validate_cli(cli_executable, home_root=plan.home_root)
            _validate_cli_on_path(cli_executable)
            cli_action = "installed"
        else:
            completed.append("CLI reused")

        if plan.install_skill:
            try:
                _install_skill(plan)
            except InstallError:
                if _path_is_occupied(plan.skill_dir):
                    completed.append("Skill path created but not validated")
                raise
            skill_action = "installed"
            completed.append("Skill installed")
        else:
            completed.append("Skill reused")
    except InstallError as exc:
        progress = ", ".join(completed) or "no companion changes completed"
        raise InstallError(
            "EvidentLoop companion installation is incomplete "
            f"({progress}); no external files were rolled back. "
            f"Resolve the reported failure, then rerun the same command. {exc}"
        ) from exc

    return EvidentLoopInstallResult(
        cli_action=cli_action,
        skill_action=skill_action,
        package_version=EVIDENTLOOP_PACKAGE_VERSION,
        skill_path=plan.skill_dir / _SKILL_ENTRYPOINT,
    )


def _install_skill(plan: EvidentLoopInstallPlan) -> None:
    if plan.npx_path is None:  # Defensive: prepare() owns prerequisite checks.
        raise InstallError("EvidentLoop Skill install requires npx")
    if plan.git_path is None:
        raise InstallError("EvidentLoop Skill install requires git")
    if _path_is_occupied(plan.skill_dir):
        raise InstallError(
            f"EvidentLoop Skill path changed after preflight: {plan.skill_dir}"
        )

    source_env = _base_child_env(plan.home_root)
    skills_cli_env = dict(source_env)
    skills_cli_env["DISABLE_TELEMETRY"] = "1"
    skills_cli_env["DO_NOT_TRACK"] = "1"
    with tempfile.TemporaryDirectory(prefix="sopify-evidentloop-") as temp_dir:
        staging_root = Path(temp_dir)
        source_root = staging_root / "source"
        _run_command(
            [
                plan.git_path,
                "clone",
                "--quiet",
                "--depth",
                "1",
                "--branch",
                EVIDENTLOOP_SKILL_TAG,
                EVIDENTLOOP_SKILL_REPOSITORY,
                str(source_root),
            ],
            env=source_env,
            label="EvidentLoop Skill source download",
        )
        resolved_commit = _run_command(
            [plan.git_path, "-C", str(source_root), "rev-parse", "HEAD"],
            env=source_env,
            label="EvidentLoop Skill source verification",
        ).stdout.strip()
        if resolved_commit != EVIDENTLOOP_SKILL_COMMIT:
            raise InstallError(
                "EvidentLoop Skill source commit changed: "
                f"expected {EVIDENTLOOP_SKILL_COMMIT}, got {resolved_commit or '(empty)'}"
            )

        source_skill = source_root / "skills" / _SKILL_NAME
        _validate_skill(source_skill)
        argv = [
            plan.npx_path,
            "--yes",
            f"skills@{SKILLS_CLI_VERSION}",
            "add",
            str(source_skill),
        ]

        if plan.adapter.is_workspace_scope:
            # Skills CLI targets Copilot through .agents/skills and a lockfile.
            # Keep those staging files out of the project and copy only the Skill.
            _run_command(
                [
                    *argv,
                    "-a",
                    str(plan.adapter.skills_cli_agent),
                    "-y",
                    "--copy",
                ],
                env=skills_cli_env,
                label="EvidentLoop Skill download",
                cwd=staging_root,
            )
            staged_skill = staging_root / _SKILLS_CLI_PROJECT_DIR / _SKILL_NAME
            _validate_skill(staged_skill)
            _copy_skill_directory(staged_skill, plan.skill_dir)
        else:
            _run_command(
                [
                    *argv,
                    "-g",
                    "-a",
                    str(plan.adapter.skills_cli_agent),
                    "-y",
                    "--copy",
                ],
                env=skills_cli_env,
                label="EvidentLoop Skill install",
                cwd=staging_root,
            )

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


def _validate_cli(executable: Path, *, home_root: Path) -> None:
    if not executable.is_absolute():
        raise InstallError("Existing EvidentLoop CLI path is not absolute")
    env = _isolated_python_env(home_root)
    doctor = _run_command(
        [str(executable), "doctor", "--json"],
        env=env,
        label="Existing EvidentLoop CLI doctor",
    )
    payload = _json_object(doctor.stdout, label="Existing EvidentLoop CLI doctor")
    if payload.get("status") != "ok":
        raise InstallError(
            "Existing EvidentLoop CLI is incompatible: doctor did not report status=ok. "
            f"Manage the existing install via {_OFFICIAL_INSTALL_GUIDE}"
        )
    python_value = payload.get("python_executable")
    python_executable = Path(str(python_value or ""))
    if not python_executable.is_absolute():
        raise InstallError(
            "Existing EvidentLoop CLI doctor did not return an absolute python_executable"
        )

    probe = _run_command(
        [str(python_executable), "-I", "-c", _COMPATIBILITY_CODE],
        env=env,
        label="Existing EvidentLoop CLI compatibility probe",
    )
    versions = _json_object(
        probe.stdout,
        label="Existing EvidentLoop CLI compatibility probe",
    )
    expected = {
        "package_version": EVIDENTLOOP_PACKAGE_VERSION,
        "schema_version": EVIDENTLOOP_SCHEMA_VERSION,
        "prompt_version": EVIDENTLOOP_PROMPT_VERSION,
    }
    if versions != expected:
        observed = ", ".join(f"{key}={versions.get(key)!r}" for key in expected)
        required = ", ".join(f"{key}={value!r}" for key, value in expected.items())
        raise InstallError(
            f"Existing EvidentLoop CLI is incompatible ({observed}); required {required}. "
            "Sopify will not replace it automatically. Manage the existing install via "
            f"{_OFFICIAL_INSTALL_GUIDE}"
        )

    help_result = _run_command(
        [str(python_executable), "-I", "-m", "evidentloop", "--help"],
        env=env,
        label="Existing EvidentLoop CLI module probe",
    )
    missing = [name for name in _REQUIRED_SUBCOMMANDS if name not in help_result.stdout]
    if missing:
        raise InstallError(
            "Existing EvidentLoop CLI is incompatible: missing subcommand(s) "
            + ", ".join(missing)
        )


def _validate_skill(skill_dir: Path) -> None:
    entrypoint = skill_dir / _SKILL_ENTRYPOINT
    if not skill_dir.is_dir() or not entrypoint.is_file():
        raise InstallError(
            f"EvidentLoop Skill directory is incomplete: expected {entrypoint}"
        )
    required_reference = skill_dir / _SKILL_REQUIRED_REFERENCE
    if not required_reference.is_file():
        raise InstallError(
            "EvidentLoop Skill directory is incomplete: missing referenced file "
            f"{required_reference}"
        )
    try:
        content = entrypoint.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise InstallError(f"EvidentLoop Skill is unreadable: {entrypoint}") from exc
    required_markers = (
        "name: evidentloop",
        f"`package_version` equal to `{EVIDENTLOOP_PACKAGE_VERSION}`",
        f"`schema_version` equal to `{EVIDENTLOOP_SCHEMA_VERSION}`",
        f"`prompt_version` equal to `{EVIDENTLOOP_PROMPT_VERSION}`",
        "references/codex-cli-isolation.md",
    )
    if any(marker not in content for marker in required_markers):
        raise InstallError(
            f"Existing EvidentLoop Skill is incompatible at {entrypoint}; "
            "Sopify will not replace it automatically. Manage the existing install via "
            f"{_OFFICIAL_INSTALL_GUIDE}"
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
    discovered = shutil.which("evidentloop")
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
