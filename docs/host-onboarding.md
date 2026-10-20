# Host onboarding recipe

For contributors adding a new AI coding host to Sopify. The goal is a repeatable
path to `BASELINE_SUPPORTED`, not a full protocol certification. Read
[issue #55](https://github.com/evidentloop/sopify/issues/55) for scope, and
[Cursor host acceptance](./cursor-host.md) as a worked example. This is a
checklist, not a new mechanism: use the installer, Doctor, catalog, and test
surfaces that already exist, and add no new editor, CLI, runtime, config file,
or hook schema for a baseline host.

## 1. Capability matrix

Probe every row in a disposable workspace before choosing a layout, recording
what you checked and how.

| Surface | What to confirm | How to confirm | If missing |
|---|---|---|---|
| Global rule file | Exact user-level path, precedence against the project rule, trust requirement. | Seed each candidate file with a unique marker; start a fresh session and ask the host to quote the marker and the path it loaded, then repeat with a project rule present. | Use a project rule or a Skill entry. Never install a global file the host does not read. |
| Project rule | Exact repo-root path, whether subdirectory rules load, merge or override against the global rule. | Same marker method from the repo root and from a subdirectory. | Use the root file only; otherwise fall back to a Skill or a single-file surface. |
| Skill discovery | Scanned global and project directories, nested `skills/parent/child/SKILL.md` support, `description` length limit, name-collision priority. | Create a throwaway Skill with a unique trigger phrase, watch the host's Skill list, invoke it, and record the loaded path. Test nesting separately; find the limit by shortening a deliberately long description. | Keep the layout flat and add one always-on rule that routes to the Skill, or use a single-file surface. |
| Asking the user | Whether a structured question tool exists, its tool name, and the plain-text fallback. | Ask a question with two options and record whether a tool call appears. This is a probe observation only; a baseline adapter needs no Python code for it. | Ask numbered plain-text questions and stop for user input; do not invent a question protocol. |
| Persistence and restart | Whether entry changes appear in the current session, a new session, or only after a restart/reload. | Change one marker and test each step in order; record the step that made it visible. | Document the required restart/reload; do not claim immediate availability. |
| Degradation | The smallest supported path when a surface is absent. | Exercise the fallback in the same workspace: project rule over global, single file over Skill discovery, plain text over a question tool, `.sopify/` files over host memory. | Use the fallback and mark the surface unsupported; do not silently widen the baseline. |

Optional surfaces are not part of the baseline: hooks, MCP registration,
launchers, and host runtimes are separate decisions, not something to add
because the host happens to support them. See
[Cursor host acceptance](./cursor-host.md) for the install-versus-behavior split
and the negative hook boundary.

## 2. Probe first, then choose the layout

Do not start by copying an existing adapter. Probe the real load surface, then
pick the smallest layout that matches it.

1. Use a disposable workspace and, where supported, a disposable home/profile.
   Never probe by changing the user's real account, proxy, model, host settings,
   or trust configuration.
2. Record the host version and the candidate Sopify SHA before probing.
3. Seed one global rule, one project rule, and one Skill, each with a unique
   marker. Common rule filenames to try: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
   `<HOST>.md`, and the host's own rules directory. Seed every same-directory
   candidate at once and ask the host to quote them in load order: that is what
   reveals which siblings are read at all, and which one wins.
4. In a fresh session, ask the host to quote the marker and the loaded path:
   this proves the host can see the file. For a CLI host, read `<host> --help`
   first and probe through its non-interactive mode (`-p`, `--print`), so every
   marker check is genuinely a new session and the transcript is reproducible.
5. Ask for one deterministic action from that file (read a named file first,
   run an existing script, emit a fixed token) and record the tool call: this
   proves the host follows the rule rather than repeating text.
6. Repeat after the required new-session/restart/reload step, then choose the
   install surface.

Keep three facts separate: **installed** (the file exists at the expected path
and matches the candidate hash), **host sees it** (the host lists, loads, or
quotes it in a fresh session), and **host follows it** (the host takes the
required action, with a transcript). A file hash or Doctor file check proves
only the first.

Reuse one of the three existing instruction surfaces in
`installer/hosts/base.py` rather than adding a new one:

- `header_embedded`: writes or updates a managed block in the host's user-level
  rule file and copies the `skills/sopify` tree into `<config_dir>/skills/sopify`
  — for hosts that read a home rule file plus a global Skill tree (Claude,
  Codex, Qoder).
- `single_file`: renders the header and the Skill tree into one self-contained
  managed block inside a workspace file — for hosts with no user-level rule
  surface that only read a project instruction file (Copilot; `skills/hosts.yaml`
  still calls it `copilot_instructions_md`).
- `user_plugin`: writes a packaged user Plugin rule plus a global Skill tree
  under the user directory — for hosts that load user-level plugin packages
  (Cursor).

## 3. Code integration and public registration

| Location | Change |
|---|---|
| `installer/hosts/<host>.py` | Add the adapter and its `HostCapability`, declaring `SupportTier.BASELINE_SUPPORTED`. Use [cursor.py](../installer/hosts/cursor.py) as the nearest example. |
| `installer/hosts/__init__.py` | Import the adapter and add it to `_REGISTRATIONS`. |
| `skills/hosts.yaml` | Add the host metadata consumed by the renderer. |
| `skills/catalog/*/skill.yaml` | Add the host id to `host_support`, then regenerate with `python3 scripts/generate-builtin-catalog.py`. |
| `installer/distribution.py` | Add the product display name in `_host_display_name`. |
| `installer/inspection.py` | Wire the Doctor/status checks, keeping install checks separate from behavior checks as Cursor does. |
| `README.md` / `README.zh-CN.md` | Add the host to the support table only once the evidence exists. |
| `docs/<host>-host.md` | Add the host acceptance doc, following [cursor-host.md](./cursor-host.md). |
| [docs/getting-started.md](./getting-started.md) | Add the host setup section only after the install path is verified. |

Declare only what you can back with evidence: a `FeatureId` belongs in
`verified_features` only when it was observed, `entry_modes` lists only what the
host actually uses, and `declared_enhancements` stays empty for a baseline. A
host passes `BASELINE_SUPPORTED` only with repeatable black-box evidence for the
protocol path in [.sopify/blueprint/protocol.md](../.sopify/blueprint/protocol.md).

## 4. Automated tests and real-session checks

Add `tests/test_<host>_host.py` for adapter registration, exact paths,
managed-block behavior, update/skip/idempotency, and Doctor check names, and
extend the shared suites: `tests/test_installer.py` (target parsing, install
actions, preservation of non-Sopify content), `tests/test_home_host_integrity.py`
or the equivalent surface test (repeat installs do not duplicate blocks),
`tests/test_installer_status_doctor.py` (host appears, install facts separated
from behavior checks), `tests/test_golden_snapshots.py`,
`tests/test_plan_contract_assets.py`, and `tests/test_plain_language_contracts.py`.
Run `python3 -m pytest tests -q` and the existing release preflight; do not add a
parallel checker.

Then run these real-session checks in a disposable workspace, recording the
transcript for each. Never pass one on a static Doctor result or a file hash
alone.

1. **Visibility** — the host quotes the unique entry marker and loaded path.
2. **Consult** — a factual question gets a direct answer; no plan, handoff, or
   receipt is created.
3. **Small fix** — a one-line edit stays a direct edit, with no workflow entry.
4. **New plan** — the documented Sopify entry (for example `~go plan`) runs the
   Analyze scoring script, asks when facts are missing, and writes only through
   `sopify_writer`.
5. **Resume** — a new session continues from `.sopify/` without a manual recap.
6. **Finalize** — an explicit finalize archives the plan and records the
   verification evidence.
7. **Negative** — without `.sopify/`, a plain question creates no workflow
   state, and optional hooks stay no-op outside a managed root.

## 5. Evidence bundle

Keep the raw transcript next to every record; do not summarize the tool calls
away.

| Field | Record |
|---|---|
| Host | Product name and exact version output (for example `traecli 0.209.1`). |
| Candidate | Branch/tag plus `git rev-parse HEAD`, and whether the install came from a local checkout or `install.sh --ref`. |
| Install | The exact `--target <host:lang>` value and the host-reported install root. |
| Paths | Home root, project root, entry rule, Skill root, payload root. |
| Hashes | SHA-256 of the entry rule, the top-level Skill, each phase Skill, and `payload-manifest.json` as actually written. |
| Session | Transcript path, start command, working directory, session id if exposed. |
| Probe | Disposable workspace path and the observed trust/approval state, unchanged. |
| Facts | `installed`, `host sees it`, and `host follows it` recorded separately. |
| Result | Pass/fail per check, with the exact reason for any skip. |

## 6. Negative boundaries

- Do not change the account, proxy, model, API key, keychain, host settings, or
  trust configuration. If trust is a variable, use an already-trusted workspace
  or a host-supported isolated profile; otherwise record it as **not verified**.
  Never bypass hook trust.
- Shared home files must be written as a managed block through the existing
  `installer.bootstrap_workspace.upsert_managed_instruction_block` path reached
  by `install_host_assets`. Never overwrite the whole file: preserve user
  content, keep repeated installs idempotent, and migrate old full-file installs
  with the existing migration path.
- A plain question must not create or modify `.sopify/` state. Q&A and small
  fixes stay direct; only `new_plan`, `continue_plan`, `finalize`, or an
  explicitly managed develop request enters the workflow, as demonstrated in
  [cursor-host.md](./cursor-host.md).
- A baseline adapter adds no hooks, MCP registration, launcher, or runtime, and
  introduces no new user-visible concept or manual upgrade step.

## 7. Definition of done

The change is ready for review when the capability matrix is filled with
evidence rather than assumptions, the install uses the smallest working surface
and preserves user content, plain questions and small fixes stay out of the
workflow, the evidence bundle is complete, the tier is `BASELINE_SUPPORTED`
unless full protocol evidence exists, and the host doc and shared tests are in
place.

Before reporting done, re-run the drift checks: re-hash the installed entry file
and Skill tree against the candidate source (`skill_tree_matches` implements the
owned-file comparison for home hosts); run
`python3 scripts/sopify_doctor.py --format json --home-root "$HOME"` and record
the host checks without treating `skip (BLACK_BOX_NOT_VERIFIED)` as a pass; run
the full test suite and the release preflight; and re-run the visibility check
after any host update. A mismatched hash, or a path that merely exists, is not a
pass.