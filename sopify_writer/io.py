"""IO utilities for canonical writer state storage."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Optional

from sopify_contracts import RuntimeHandoff


def read_json(path: Path) -> Optional[dict[str, Any]]:
    """Read a JSON state file if it exists."""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomically write a JSON payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temp_path = Path(handle.name)
    temp_path.replace(path)


def write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    """Atomically create a JSON file and fail if the target already exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with NamedTemporaryFile(
            "w", delete=False, dir=path.parent, encoding="utf-8"
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            temp_path = Path(handle.name)

        # Linking a complete same-directory temp file is an atomic exclusive
        # create: concurrent writers cannot replace an existing receipt.
        os.link(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def read_runtime_handoff(path: Path) -> RuntimeHandoff | None:
    """Read a handoff file if it exists."""
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    return RuntimeHandoff.from_dict(payload)
