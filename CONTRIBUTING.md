# Contributing

Agree on scope and ownership before non-trivial work. Keep a pull request focused on one verifiable change; update both READMEs for user-facing changes and add a short CHANGELOG note for user-visible behavior or maintainer-command changes.

## How to contribute

- `main` is the only long-lived branch. Use short-lived `<type>/<topic>` branches and normally merge through PRs; stable versions are tags and GitHub Releases from merged `main` commits. Reconsider a release branch only when concurrent supported versions require backports.
- Fix the current failure chain without adding unrelated routes, state or features. Put deferred work in the relevant plan or backlog.
- Preserve existing work. Explicitly include new source files when preparing a commit; `git commit -am` does not include them.
- Changes to protocol, checkpoint, bridge, installer or status/doctor behavior need corresponding regression evidence. Documentation-only work needs relevant link/content checks, not unrelated code tests.

## Prompt-layer and Skill Authoring

`skills/{zh,en}` is the single prompt source: `header.md.template` plus `skills/sopify/`. Keep both languages aligned and follow their Skill entry files. Installation products come from adapters; do not hand-maintain a second source tree.

Preview one header from the repository root:

```bash
python3 scripts/render-host-skills.py --host codex --lang zh --output /tmp/sopify-preview/AGENTS.md
```

Omit `--output` for stdout, or use `--verify-all` to compare all header variants. This previews headers only; inspect Skill bodies in `skills/{zh,en}/skills/sopify/`. Old `Codex/` and `Claude/` cache directories remain gitignored and are not release inputs.

- Bind routes through `supports_routes` and validate `skill.yaml` with `sopify_contracts/skill_schema.py`.
- `tools / disallowed_tools / allowed_paths / requires_network` are declarative fields.
- When catalog metadata changes, regenerate `skills/catalog/builtin_catalog.generated.json` with `python3 scripts/generate-builtin-catalog.py` rather than editing the generated catalog.
- Review intentional output changes before running `python3 scripts/regenerate-golden-snapshots.py`; preflight checks snapshots and does not accept drift automatically.

## Payload Bundle and Host Integration

Use the [host onboarding recipe](./docs/host-onboarding.md) for capability probes and adapter changes. The [Protocol](./.sopify/blueprint/protocol.md) defines entry and write ownership; `sopify_writer` owns protocol state writes. The workspace marker locates a bundle, while plan files own task progress.

- Keep root `install.sh` / `install.ps1` thin: fetch the same-ref archive and call `scripts/install_sopify.py`.
- Distribution remains host-registry driven. Preserve legacy bundle reads and standalone helper/Hook fallbacks.
- Installation, update, optional components and removal are documented in [Getting Started](./docs/getting-started.md). Developer `raw/main` installs are not the public README entry.

### MCP pilot

The repo-local `scripts/sopify_mcp_server.py` pilot uses an existing Python 3.11+ environment with `mcp[cli]>=1.27,<2`; it does not install dependencies or change the payload.

```bash
# Inspect registration; dry-run is the default.
python3 scripts/sopify_mcp_register.py --python /path/to/python3
# Explicitly apply through the host's official CLI.
python3 scripts/sopify_mcp_register.py --python /path/to/python3 --apply
```

Registration delegates to `codex mcp get/add`, not direct TOML edits. Matching settings are a no-op and conflicting settings are not overwritten. Codex is the first validation target; other hosts, dependency packaging and doctor integration need their own evidence.

## Validation Commands

Use Python 3.11+ and checks appropriate to the change. Shared-workspace runs can set `PYTHONDONTWRITEBYTECODE=1` and `PYTEST_ADDOPTS="-p no:cacheprovider"` to avoid cache noise.

```bash
python3 -m pytest tests -q
python3 scripts/check-readme-links.py
```

For protocol/payload work, also run the relevant smoke:

```bash
python3 scripts/sopify_protocol_check.py check --scenario new-plan --fixture tests/fixtures/minimal_plan
python3 scripts/check-install-payload-bundle-smoke.py --target codex:zh-CN
```

## Release Hook and CHANGELOG

[Release Process](./docs/dev/release-process.md) is the single source for hook setup, version/CHANGELOG synchronization, preflight, stable assets, publication and post-release smoke. Follow the authorization for the current task before any external Git action.

## License Note

AI collaboration is acknowledged in [CONTRIBUTORS.md](./CONTRIBUTORS.md). Standard AI `Co-authored-by` trailers are not added automatically; manual coauthor attribution remains available.

Contributions follow the target file's license: code/configuration use Apache 2.0; documentation uses CC BY 4.0.
