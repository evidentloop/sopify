#!/usr/bin/env python3
"""Internal helper for host-side long-term preference preload.

This helper does not replace the default Sopify runtime entry. Hosts may call
it before invoking Sopify LLM rounds so they do not need to reimplement the
workspace config lookup and preference-path resolution rules.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.config import ConfigError
from runtime.preferences import preload_preferences_for_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect Sopify long-term preference preload for a workspace.")
    parser.add_argument(
        "--workspace-root",
        default=".",
        help="Target workspace root. Defaults to the current directory.",
    )
    parser.add_argument(
        "--global-config-path",
        default=None,
        help="Optional override for the global sopify config path.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("inspect", help="Resolve and read workspace preferences.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    workspace_root = Path(args.workspace_root).resolve()

    try:
        if args.command != "inspect":
            raise ValueError(f"Unsupported command: {args.command}")
        result = preload_preferences_for_workspace(
            workspace_root,
            global_config_path=args.global_config_path,
        )
    except (ConfigError, ValueError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(
        json.dumps(
            {
                "status": "ready",
                "preferences": result.to_dict(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
