# Contributing

Thanks for your interest in contributing to Sopify.

## How to contribute

- Open an issue first for non-trivial changes so scope and ownership are clear.
- Keep pull requests focused; one feature or fix per PR is preferred.
- Update both `README.md` and `README.zh-CN.md` when user-facing behavior changes.
- Update `CHANGELOG.md` manually when user-visible behavior or maintainer rules change.

## Prompt-layer and Skill Authoring

- `skills/{zh,en}` is the prompt-layer source of truth. Each language directory contains `header.md.template` (host-agnostic template) and `skills/sopify/` (skill packages).
- `Codex/Skills/{CN,EN}` and `Claude/Skills/{CN,EN}` are gitignored. They can be generated locally via `bash scripts/sync-skills.sh` for debugging or inspecting the traditional host layout, but are not part of release, CI, or pre-commit.
- `skills/catalog/builtin_catalog.generated.json` is the generated builtin catalog, maintained via `scripts/generate-builtin-catalog.py`.
- For skill package changes, follow the `SKILL.md` files under [skills/zh/skills/sopify/](./skills/zh/skills/sopify/) / [skills/en/skills/sopify/](./skills/en/skills/sopify/).

Key constraints:

- Prefer `supports_routes` for route binding.
- Validate `skill.yaml` through `sopify_contracts/skill_schema.py`.
- `tools / disallowed_tools / allowed_paths / requires_network` are currently declarative fields.
- Regenerate the builtin catalog instead of editing generated metadata manually.

## Payload Bundle and Host Integration

Use these commands when you need maintainer-level control over the payload bundle:

```bash
# Validate install + payload bundle + workspace stub in isolation
python3 scripts/check-install-payload-bundle-smoke.py --target codex:zh-CN

# Run protocol compliance check
python3 scripts/sopify_protocol_check.py check --scenario new-plan --fixture tests/fixtures/minimal_plan
```

Bundle rules:

- The global payload lives under `~/.codex/sopify/` or `~/.claude/sopify/`.
- Hosts must read `.sopify-skills/sopify.json` to detect workspace activation and resolve the selected global bundle.
- The host follows the 4-step protocol entry contract (active_plan → plan.md → current_handoff → receipts) defined in `.sopify-skills/blueprint/protocol.md §8`.
- Protocol state writes go through `sopify_writer`; hosts do not write state files directly.

### Installer Entry Points and Release Assets

Current installer entry points are intentionally split by audience:

- Repo-local / source install:

```bash
bash scripts/install-sopify.sh --target codex:zh-CN
python3 scripts/install_sopify.py --target claude:en-US --workspace /path/to/project
```

- Dev / maintainer remote entry (`raw/main`, not for README first screen):

```bash
curl -fsSL https://raw.githubusercontent.com/evidentloop/sopify/main/install.sh | \
  bash -s -- --target codex:zh-CN
```

- Public stable entry (only after a public GitHub Release exists):

```bash
curl -fsSL https://github.com/evidentloop/sopify/releases/latest/download/install.sh | \
  bash -s -- --target codex:zh-CN
```

Contract:

- Root `install.sh` / `install.ps1` stay thin. They only fetch the same-ref GitHub source archive and call `scripts/install_sopify.py`.
- `main` branch root scripts keep dev defaults (`SOURCE_CHANNEL=dev`, `SOURCE_REF=main`).
- Stable release assets are rendered from the root scripts for the selected release tag; do not hand-edit or upload the raw `main` files.
- Distribution logic stays host-registry driven. README should expose the host availability matrix, including experimental install targets once the repo-side path is ready, and the installer entrypoint must not hardcode `codex` / `claude` branching.

Release asset checklist:

```bash
TAG="2026-03-25.142231"
OUT_DIR="$(mktemp -d)"
python3 scripts/render-release-installers.py --release-tag "$TAG" --output-dir "$OUT_DIR"
```

Then:

- Upload `$OUT_DIR/install.sh` and `$OUT_DIR/install.ps1` to the GitHub Release with the same tag.
- Keep `README` first-screen install commands unchanged until that public stable release is visible at `releases/latest/download/install.sh`.
- Post-release manual smoke is maintainer-only: confirm the latest release assets exist, the stable installer resolves the same tag, and the install output prints `source channel`, `resolved source ref`, and `asset name`.

## Validation Commands

Run the minimum checks that match your change scope.

Prompt-layer and metadata sync:

```bash
bash scripts/check-version-consistency.sh
python3 scripts/generate-builtin-catalog.py
python3 -m pytest tests -v
```

Protocol and payload validation:

```bash
python3 scripts/sopify_protocol_check.py check --scenario new-plan --fixture tests/fixtures/minimal_plan
python3 scripts/check-install-payload-bundle-smoke.py --target codex:zh-CN
python3 -m pytest tests -v
```

Documentation and release validation:

```bash
python3 scripts/check-readme-links.py
python3 -m unittest tests/test_release_hooks.py -v
python3 -m unittest tests/test_distribution.py tests/test_installer_status_doctor.py -v
bash scripts/check-version-consistency.sh
```

## Release Hook and CHANGELOG

This repository ships coordinated `.githooks/pre-commit` and `commit-msg` automation.

Enable it once per clone:

```bash
git config core.hooksPath .githooks
```

Behavior summary:

- `pre-commit` runs `scripts/release-preflight.sh` and then `scripts/release-sync.sh`.
- Release-managed files are re-staged into the same commit when checks pass.
- When `CHANGELOG.md -> [Unreleased]` is empty, `release-sync` auto-drafts summary-level notes (category bullets, no per-file lists) from the current staged files.
- `commit-msg` only appends `Release-Sync`, `Release-Version`, and `Release-Date` when the pre-commit handoff exists.

AI attribution:

- AI collaboration is acknowledged at the repository level in [CONTRIBUTORS.md](./CONTRIBUTORS.md).
- The repository no longer appends standard `Co-authored-by` trailers for AI assistants by default, so GitHub contributor attribution remains tied to human commit authors unless you add co-author trailers manually.
- `SOPIFY_DISABLE_RELEASE_HOOK=1` disables the entire release hook chain; use it only for maintainer/debug flows.

Common environment toggles:

- `SOPIFY_DISABLE_RELEASE_HOOK=1`
- `SOPIFY_SKIP_RELEASE_PREFLIGHT=1`
- `SOPIFY_AUTO_DRAFT_CHANGELOG=0`
- `SOPIFY_RELEASE_HOOK_DRY_RUN=1`
- `SOPIFY_FORCE_RELEASE_SYNC=1`

## License Note

By contributing, you agree that your changes may be distributed under the license that applies to the files you modify:

- Code and config: Apache 2.0
- Documentation: CC BY 4.0
