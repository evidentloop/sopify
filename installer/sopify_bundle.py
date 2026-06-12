"""Helpers for syncing the Sopify payload bundle into a workspace.

P8 (Protocol Kernel & Runtime Retirement): the "runtime bundle" concept has
been retired. This module now syncs only the protocol-kernel assets
(sopify_contracts + sopify_writer) into a versioned payload bundle.
The runtime/ directory, runtime scripts, and runtime manifest are no longer
shipped. The bundle manifest is written inline without importing from
runtime.manifest.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil

from installer.models import InstallError

DEFAULT_PAYLOAD_BUNDLE_DIRNAME = ".sopify-payload"

# P8: runtime removed — only protocol-kernel packages remain
_DIRECTORY_ASSETS = ("sopify_contracts", "sopify_writer")
_CATALOG_SOURCE_RELATIVE = Path("skills") / "catalog" / "builtin_catalog.generated.json"
_CATALOG_BUNDLE_RELATIVE = Path("catalog") / "builtin_catalog.generated.json"
_COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def sync_payload_bundle(
    repo_root: Path,
    workspace_root: Path,
    *,
    bundle_dirname: str = DEFAULT_PAYLOAD_BUNDLE_DIRNAME,
    bundle_version: str | None = None,
) -> Path:
    """Sync the protocol-kernel payload bundle into the target workspace."""
    resolved_repo_root = repo_root.resolve()
    resolved_workspace_root = workspace_root.resolve()
    if not resolved_workspace_root.is_dir():
        raise InstallError(f"Target root does not exist: {workspace_root}")

    bundle_path = Path(bundle_dirname)
    bundle_root = bundle_path if bundle_path.is_absolute() else resolved_workspace_root / bundle_path

    required_sources = tuple(resolved_repo_root / name for name in _DIRECTORY_ASSETS)
    catalog_source = resolved_repo_root / _CATALOG_SOURCE_RELATIVE
    missing_sources = [path for path in (*required_sources, catalog_source) if not path.exists()]
    if missing_sources:
        raise InstallError(f"Missing required source asset: {missing_sources[0]}")

    try:
        bundle_root.mkdir(parents=True, exist_ok=True)
        for name in _DIRECTORY_ASSETS:
            _replace_tree(resolved_repo_root / name, bundle_root / name)

        catalog_dest = bundle_root / _CATALOG_BUNDLE_RELATIVE
        catalog_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(catalog_source, catalog_dest)

        _write_payload_bundle_manifest(
            bundle_root=bundle_root,
            source_root=resolved_repo_root,
            bundle_version=bundle_version,
        )
    except OSError as exc:
        raise InstallError(f"Payload bundle sync failed: {exc}") from exc

    required_paths = (
        bundle_root / "manifest.json",
        bundle_root / "sopify_contracts" / "__init__.py",
        bundle_root / "sopify_writer" / "__init__.py",
        bundle_root / _CATALOG_BUNDLE_RELATIVE,
    )
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        raise InstallError(f"Payload bundle sync incomplete: {missing[0]}")
    return bundle_root


def _write_payload_bundle_manifest(
    *,
    bundle_root: Path,
    source_root: Path,
    bundle_version: str | None = None,
) -> None:
    """Write a minimal bundle manifest without importing from runtime.manifest.

    P8 replaced the runtime-generated manifest (which transitively imported 8+
    runtime submodules) with this inline writer that captures only the
    protocol-kernel metadata needed by the installer and bootstrap helper.

    W0.7: version resolution is explicit parameter > sopify_contracts.__version__
    > SOPIFY_DEV_VERSION env var (must be a valid version string). If none
    resolves, raises InstallError instead of silently falling back to "0.0.0-dev".
    """
    from sopify_writer import iso_now

    resolved_version = bundle_version or _read_contracts_version(source_root) or _read_dev_version()
    if not resolved_version:
        raise InstallError(
            "Bundle version could not be resolved: no explicit version provided, "
            "sopify_contracts.__version__ not found, and SOPIFY_DEV_VERSION not set. "
            "Pass bundle_version explicitly or set SOPIFY_DEV_VERSION to a valid version string "
            "(e.g. SOPIFY_DEV_VERSION=0.0.0-dev.local)."
        )

    manifest = {
        "schema_version": "1",
        "bundle_version": resolved_version,
        "generated_at": iso_now(),
        "capabilities": {
            "bundle_role": "control_plane",
            "manifest_first": True,
            "writes_handoff_file": True,
        },
        "dependency_model": {
            "mode": "stdlib_only",
            "python_min": "3.11",
            "host_env_dir": None,
            "runtime_dependencies": [],
        },
        "directory_assets": list(_DIRECTORY_ASSETS),
        "catalog_path": str(_CATALOG_BUNDLE_RELATIVE),
    }
    manifest_path = bundle_root / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def _read_contracts_version(source_root: Path) -> str | None:
    """Read __version__ from sopify_contracts/__init__.py, return None if absent."""
    version_path = source_root / "sopify_contracts" / "__init__.py"
    if not version_path.is_file():
        return None
    for line in version_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("__version__"):
            _, _, raw = stripped.partition("=")
            candidate = raw.strip().strip("'\"")
            if candidate:
                return candidate
    return None


def _read_dev_version() -> str | None:
    """Read SOPIFY_DEV_VERSION env var. Bare boolean '1'/'true' is NOT accepted."""
    dev_value = os.environ.get("SOPIFY_DEV_VERSION", "").strip()
    if not dev_value:
        return None
    if dev_value.lower() in ("1", "true", "yes"):
        raise InstallError(
            "SOPIFY_DEV_VERSION is set to a bare boolean value. "
            "Provide an explicit dev channel version string, "
            "e.g. SOPIFY_DEV_VERSION=0.0.0-dev.local"
        )
    return dev_value


def _replace_tree(source_root: Path, destination_root: Path) -> None:
    _remove_existing_path(destination_root)
    shutil.copytree(source_root, destination_root, ignore=_COPY_IGNORE)


def _remove_existing_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        return
    path.unlink()
