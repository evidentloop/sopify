# Batch 3 Observations: rs-sdk

## Scope

- Batch: `batch_3`
- Repo: `rs-sdk`
- Path: `/Users/weixin.li/NIO_Project/rs-sdk`
- Samples: `RS-01` to `RS-15`
- Role: `sdk/tool + quick-fix/control validation`
- Status: `completed`

## Setup

- Review mode: repo-grounded manual calibration review against the current phase-1 first-principles boundary
- Execution date: `2026-03-22`
- Reviewer: `codex`
- Local repo policy: keep `rs-sdk` read-only during pilot recording
- Batch note: this batch emphasizes sdk/tool architecture questions plus a heavier control mix than Batch 2

## Repo Readiness

- Local git status at review time: clean
- Guardrail: keep control samples lightweight; do not let docs / CLI / naming tweaks drift into challenge-heavy flows
- Existing repo context already present:
  - root `package.json` uses `lerna run build:doc/build:lib --since` as the shared orchestrator
  - `doc-sites` is a workspace package and a separate VitePress site, not just generated markdown output
  - `hooks` already exports `useFetch`, `useNativeFetch`, `useOptimizeImage`, and interceptor plumbing
  - `config-provider` already contains both `OfflineConfigProvider` and `RuntimeConfigProvider`
  - `packages/cli` is still lightweight and currently exposes only `init`
  - `@rs-sdk/shared` exists, but is currently a thin engineering/shared-config package rather than a rich runtime utility layer

## Observation Notes

Use this file for narrative evidence that does not fit cleanly in the review sheet:

- where architecture questions benefited from challenge mode
- where sdk/tool path corrections were genuinely lower-cost
- where quick fixes stayed clean
- where pure consult requests stayed direct

## Batch Summary

- Batch 3 validates the current trigger boundary well. `A2/A3/A4` questions map to real codebase boundaries rather than hypothetical abstraction debates.
- The caution carried over from Batch 2 remained useful, but did not block progress. `A4` questions in `rs-sdk` are more grounded because the repo already exposes package, build, and doc split points directly in code and config.
- Control protection is strong in this repo. Docs-only, CLI-text, and naming-alignment requests all remain obvious `direct_no_trigger` samples.
- The main calibration gain from Batch 3 is sharper wording for sdk/tool scenarios: challenge should focus on “existing package contract or pipeline boundary” instead of generic “architecture depth”.

## Route Summary

| sample_id | label | assessed_behavior | helpfulness | reviewer_note |
| --- | --- | --- | --- | --- |
| `RS-01` | `A4` | `consult_challenge_trigger` | `helpful` | Shared orchestration already exists at root, but package-level build/doc ownership remains split. |
| `RS-02` | `A2` | `consult_challenge_trigger` | `helpful` | Copying business fetch logic into `hooks` would violate the generic package boundary. |
| `RS-03` | `A3` | `consult_challenge_trigger` | `helpful` | `@rs-sdk/shared` exists, but not as a mature prompt/template abstraction layer. |
| `RS-04` | `A1` | `light_clarification` | `helpful` | “接入体验” is too broad without one narrowing question. |
| `RS-05` | `A4` | `consult_challenge_trigger` | `helpful` | Offline/runtime config capability already coexists; the real decision is whether to keep the split explicit. |
| `RS-06` | `A3` | `consult_challenge_trigger` | `helpful` | `useRequest` likely overlaps with existing `useFetch/useNativeFetch`. |
| `RS-07` | `A4` | `consult_challenge_trigger` | `helpful` | README, story docs, and doc-sites already form a genuine source-of-truth split. |
| `RS-08` | `C1` | `direct_no_trigger` | `n/a` | README typo remains lightweight. |
| `RS-09` | `C1` | `direct_no_trigger` | `n/a` | CLI `--help` wording is a bounded tweak. |
| `RS-10` | `C2` | `direct_no_trigger` | `n/a` | Pure responsibility explanation stays direct. |
| `RS-11` | `C1` | `direct_no_trigger` | `n/a` | Adding a doc link remains lightweight. |
| `RS-12` | `C1` | `direct_no_trigger` | `n/a` | CLI banner wording stays in quick-fix territory. |
| `RS-13` | `C2` | `direct_no_trigger` | `n/a` | Current subcommand inventory is a direct answer. |
| `RS-14` | `C1` | `direct_no_trigger` | `n/a` | Script naming alignment remains a bounded edit. |
| `RS-15` | `C2` | `direct_no_trigger` | `n/a` | README self-consistency review stays as a direct consult/review. |

## Sample-Level Evidence

### RS-01

- Request: `hooks` 和 `config-provider` 要不要继续共用一套 build/doc pipeline，还是按包拆开？
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - root `package.json` already orchestrates package builds through `lerna run build:doc/build:lib --since`
  - `hooks` and `config-provider` each still own their own `build:doc/build:lib/dev` scripts
  - `doc-sites` is a separate workspace package
- Reviewer note: This is a real pipeline-boundary question, not an abstract architecture detour.

### RS-02

- Request: 业务项目里的 fetch 逻辑我想直接复制进 `hooks` 包，先这样快点上线。
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - `hooks` already exports generic `useFetch` and `useNativeFetch`
  - request/response interceptors are extensible
- Reviewer note: Strong `A2` sample. The path should be challenged before anyone copies business-specific fetch behavior into the shared package.

### RS-03

- Request: `rs-cli` 新增模板生成时，是否应该先复用现有 shared utils，而不是重写一套 prompts 流程？
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - `@rs-sdk/shared` exists under `unpkg/shared`
  - current exported surface is thin (`deepMerge`, eslint config), not a mature CLI prompt abstraction
  - `packages/cli` currently uses local `prompts`
- Reviewer note: The useful intervention is to reject default reuse pressure when the existing shared package does not actually fit the target problem.

### RS-04

- Request: 优化 `config-provider` 的接入体验。
- Assessed behavior: `light_clarification`
- Repo facts:
  - `config-provider` covers both offline webpack injection and runtime registration
  - docs currently span README and story markdown
- Reviewer note: One clarifier is justified here because “接入体验” could refer to API shape, docs discoverability, or project wiring.

### RS-05

- Request: `config-provider` 要不要统一合并 offline 配置和 runtime 配置能力？
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - package source already defines `OfflineConfigProvider` and `RuntimeConfigProvider`
  - the current repo shape intentionally separates compile-time and runtime behavior
- Reviewer note: Helpful trigger. The right conversation is about contract clarity, not merely merging two class names.

### RS-06

- Request: 想在 `hooks` 里新增一套 `useRequest`，先帮我判断是不是重复建设。
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - `useFetch` already wraps axios instance creation and interceptors
  - `useNativeFetch` already covers app/native transport fallback
- Reviewer note: This is a straightforward lower-cost alternative sample; the trigger protects against parallel abstractions with little added value.

### RS-07

- Request: `doc-sites` 和各 package 的 README，到底谁应该是真正文档源？
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - root README is high-level and sparse
  - `hooks/README.md` is minimal, effectively pointing users to stories
  - `config-provider` has a fuller README and story markdown
  - `doc-sites` auto-generates `hooks` docs but not a full package-wide unified source
- Reviewer note: This is an excellent `A4` sample because the repo already demonstrates document-source drift.

### RS-08

- Request: 修 `hooks` README 里一个示例拼写问题。
- Assessed behavior: `direct_no_trigger`
- Repo facts:
  - bounded README typo/doc example request
- Reviewer note: Clean control sample.

### RS-09

- Request: 给 `rs-cli` 增加 `--help` 文案说明。
- Assessed behavior: `direct_no_trigger`
- Repo facts:
  - current CLI uses commander and has minimal command surface
- Reviewer note: Adding help text should remain a direct edit.

### RS-10

- Request: 解释一下 `hooks` 和 `config-provider` 的职责区别。
- Assessed behavior: `direct_no_trigger`
- Repo facts:
  - `hooks` focuses on request/env/image helpers
  - `config-provider` focuses on offline/runtime config injection and retrieval
- Reviewer note: Pure consult; no challenge needed.

### RS-11

- Request: 给 `config-provider` 的 story 文档补一个 README 链接。
- Assessed behavior: `direct_no_trigger`
- Repo facts:
  - current docs are already split across README and story markdown
- Reviewer note: Still just a doc link tweak, not a strategy question.

### RS-12

- Request: 调整 CLI banner 文案和输出样式。
- Assessed behavior: `direct_no_trigger`
- Repo facts:
  - banner is currently emitted from `packages/cli/src/index.js`
- Reviewer note: The request stays bounded even though the CLI itself is a product surface.

### RS-13

- Request: 看下 `packages/cli` 现在支持哪些子命令。
- Assessed behavior: `direct_no_trigger`
- Repo facts:
  - current commander setup only registers `init`
- Reviewer note: Another clean consult control.

### RS-14

- Request: 把某个 package 的测试脚本命名和根脚本对齐。
- Assessed behavior: `direct_no_trigger`
- Repo facts:
  - root uses orchestration-style script names
  - package-level names already vary between `test`, `test:watch`, `coverage`
- Reviewer note: Naming alignment is still a bounded cleanup ask, not an architecture fork.

### RS-15

- Request: 帮我 review 一下 `config-provider` README 的使用说明是否自洽。
- Assessed behavior: `direct_no_trigger`
- Repo facts:
  - this is a review of an existing document, not a request to redesign package boundaries
- Reviewer note: Should remain direct and lightweight.

## Interim Calibration Notes

- Trigger boundary observations:
  - Batch 3 shows the current trigger wording transfers well to sdk/tool repos when the repo already exposes package boundaries explicitly.
  - `A4` is more consistently helpful here than in Batch 2 because pipeline, package, and doc splits are already first-class artifacts in the codebase.
  - `A1` still benefits from a single factual narrowing step when the ask is experience-oriented rather than boundary-oriented.
- sdk/tool-side false positives:
  - none observed in this 15-sample review
- sdk/tool-side false negatives:
  - none observed in this 15-sample review
- quick-fix/control regression notes:
  - no control regression observed; this batch provides the stronger quick-fix/control confidence that Batch 2 could not provide because it had only one control sample
