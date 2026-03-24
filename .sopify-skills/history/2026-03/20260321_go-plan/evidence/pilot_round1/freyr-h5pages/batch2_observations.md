# Batch 2 Observations: freyr-h5pages

## Scope

- Batch: `batch_2`
- Repo: `freyr-h5pages`
- Path: `/Users/weixin.li/NIO_Project/EQUITY/freyr-h5pages`
- Samples: `FH5-01` to `FH5-15`
- Role: `business validation`
- Status: `completed`

## Setup

- Review mode: repo-grounded manual calibration review against the current phase-1 first-principles boundary
- Execution date: `2026-03-22`
- Reviewer: `codex`
- Target repo write policy: read-only for pilot evidence; no artifact was written into `freyr-h5pages`
- Evidence style: link each reviewed row back to this file anchor rather than storing pilot notes in the target repo
- Batch note: unlike Batch 1, this batch validates business-repo trigger usefulness more than runtime harness routing internals

## Repo Readiness

- Local git status at review time: dirty (`?? algorithms/`)
- Guardrail: do not write pilot evidence into the target repo
- Existing business context already present in repo:
  - NIO app already has a full `firstOwnerFiling` route tree under `/first_owner_filing` plus offline alias `/module_10603/first_owner_filing`
  - NIO config already includes `firstOwnerApiBaseUrl`, `firstOwnerApiPaths`, `polarisConfigKey.filingDetail`, tracker, and APM config
  - `shared/Layout.vue` is already consumed by the filing pages; the repo is not starting from a blank page/component baseline
  - root `scripts/load-env.js` plus shared debug-account helpers already support per-brand local debug
  - data access is already layered as `@nio-wad/hooks.fetch` plus page/domain-specific API wrappers such as `FirstOwnerGateway`

## Observation Notes

Use this file for narrative evidence that does not fit cleanly in the review sheet:

- where business-side over-trigger showed up
- where a lower-cost alternative was materially helpful
- where clarification stayed acceptably light
- where control samples remained clean

## Batch Summary

- The current boundary remains useful in this repo because many requests only look greenfield on the surface; repo evidence often reveals an existing filing flow, gateway, or config split that materially changes the recommended path.
- `A2/A3` performed especially well in business context. Requests that proposed modal shortcuts, local copies, one-off alias fixes, or a new global fetch layer were all improved by first challenging the path.
- `A1` remains valid, but business-side ambiguity works best with one factual clarifier first. `FH5-05`, `FH5-10`, and `FH5-13` are better as `light_clarification` than as a broader abstract challenge.
- `A4` is still mostly useful, but wording can get too abstract when the repo does not already expose the same abstraction boundary in code. `FH5-14` is the clearest caution sample.

## Route Summary

| sample_id | label | assessed_behavior | helpfulness | reviewer_note |
| --- | --- | --- | --- | --- |
| `FH5-01` | `A1` | `consult_challenge_trigger` | `helpful` | Existing filing flow turns the ask into extension analysis rather than greenfield page discovery. |
| `FH5-02` | `A2` | `consult_challenge_trigger` | `helpful` | The proposed `charging_piles` modal is a shortcut that conflicts with the existing dedicated filing flow. |
| `FH5-03` | `A4` | `consult_challenge_trigger` | `helpful` | Brand split is real because only NIO currently has filing-specific config and API wiring. |
| `FH5-04` | `A3` | `consult_challenge_trigger` | `helpful` | Copying shared Layout is a higher-cost local fork than wrapper/prop extension. |
| `FH5-05` | `A1` | `light_clarification` | `helpful` | Offline experience is ambiguous across alias, root redirect, hash mode, and app guard. |
| `FH5-06` | `A4` | `consult_challenge_trigger` | `helpful` | Static config vs Polaris remote config is already an explicit contract split in the repo. |
| `FH5-07` | `A3` | `consult_challenge_trigger` | `helpful` | Existing draft APIs make “local cache” a likely overbuild. |
| `FH5-08` | `A4` | `consult_challenge_trigger` | `helpful` | Tracking is cross-brand but not fully uniform; common baseline plus page-specific events is the real design question. |
| `FH5-09` | `A2` | `consult_challenge_trigger` | `helpful` | Router alias alone does not equal offline support because the flow already depends on more than one route concern. |
| `FH5-10` | `A1` | `light_clarification` | `helpful` | “Make the homepage clearer” needs scope narrowing before proposing any path. |
| `FH5-11` | `A4` | `consult_challenge_trigger` | `helpful` | Shared-component placement should follow actual cross-brand reuse, not speculative reuse. |
| `FH5-12` | `A3` | `consult_challenge_trigger` | `helpful` | Another global fetch layer would duplicate existing hooks + page gateway layering. |
| `FH5-13` | `A1` | `light_clarification` | `helpful` | Debug flow already exists in partial form; the first step is identifying which brand/env remains unstable. |
| `FH5-14` | `A4` | `consult_challenge_trigger` | `neutral` | The trigger is directionally right, but `provider` language outruns the current repo abstractions. |
| `FH5-15` | `C1` | `direct_no_trigger` | `n/a` | README docs completion stays a bounded quick-fix. |

## Sample-Level Evidence

Record transcript, screenshot, or conversation links here while filling `pilot_round1_review_sheet.md`.

### FH5-01

- Request: 在权益中心支持“首任车主备案 V2.0”，先帮我分析要落哪些页面和模块。
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - `apps/cn/nio/src/router/index.ts` already defines the filing base route plus `guide/records/vehicle/step1/step2/step3/result/detail/rules`
  - `apps/cn/nio/src/pages/firstOwnerFiling/apis/FirstOwnerGateway.ts` and related API files already exist
- Reviewer note: The useful intervention is to reframe the ask from “what new pages do we need” to “which parts of the existing filing flow need V2.0 extension”.

### FH5-02

- Request: 直接在 `charging_piles` 页面里塞一个备案弹窗，先这样做最快。
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - `charging_piles` is a separate route and business flow
  - filing already has its own route tree, store, and gateway layer
- Reviewer note: Challenging the path is clearly useful here; the request optimizes for apparent speed while ignoring existing structure.

### FH5-03

- Request: NIO、Alps、Firefly 的备案页是共用一套，还是按品牌拆开做？
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - only NIO config includes `firstOwnerApiBaseUrl`, `firstOwnerApiPaths`, and `polarisConfigKey.filingDetail`
  - Alps/Firefly configs do not expose the same filing contract today
- Reviewer note: This is a real architecture boundary question, not a presentational discussion.

### FH5-04

- Request: 想把 `shared` 里的 Layout 复制到 `apps/cn/nio` 本地改，避免影响别的品牌。
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - filing pages already import `@freyr-h5pages/shared/src/components/layout/Layout.vue`
  - shared Layout is a common dependency across pages and brands
- Reviewer note: The lower-cost alternative is to extend or wrap shared Layout, not clone it.

### FH5-05

- Request: 优化 offline 包访问备案页的体验。
- Assessed behavior: `light_clarification`
- Repo facts:
  - filing routes already have offline aliases
  - router also contains offline root redirect, hash/history switching, and in-app access guard
- Reviewer note: The correct first move is a single clarifier on which part of offline access feels bad, rather than launching into broad architecture advice.

### FH5-06

- Request: 新页面配置放 `default.config.json`，还是走 Polaris 远端配置？
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - `default.config.json` stores base URL, API paths, and tracker/APM ids
  - Polaris is already used for dynamic keys such as `filingDetail`
- Reviewer note: The current repo already expresses a config boundary that the answer should make explicit.

### FH5-07

- Request: 备案流程想加本地缓存，避免重复填写，先帮我判断最小改法。
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - filing APIs already include `draftSave` and `draftDetail`
  - filing store already tracks flow state and selected vehicle
- Reviewer note: The intervention is useful because the cheapest solution is likely “lean harder on existing draft persistence”, not “add new local cache infra”.

### FH5-08

- Request: 多品牌埋点是走统一 tracker 规则，还是页面自己各自打点？
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - all brands expose tracker/apm config in app config
  - NIO filing already has a page-level APM reporter hook
  - Firefly contains more explicit `nio-tracker-web` usage
- Reviewer note: A common baseline plus page-specific business events is the real boundary worth surfacing.

### FH5-09

- Request: 只要补一个 router hash alias，就算支持离线备案页了吧？
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - filing routes already include offline aliases
  - offline behavior also depends on the top-level redirect and route mode selection
- Reviewer note: This is a clean `A2` sample because the proposed path already exists and still would not fully solve the problem.

### FH5-10

- Request: 把权益中心首页改得更清晰一点，但我还没想好范围。
- Assessed behavior: `light_clarification`
- Repo facts:
  - repo contains multiple “home/index” style entry pages across brands
  - no specific success metric or page target is supplied in the request
- Reviewer note: One narrowing question is enough and keeps the business ask from getting heavier than necessary.

### FH5-11

- Request: 通用备案表单组件应该放 `shared/`，还是先只在 `apps/cn/nio` 落地？
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - only NIO has a production-like filing flow today
  - shared already hosts layout/common utilities, but not filing-specific form components
- Reviewer note: The useful challenge is to demand evidence of cross-brand reuse before moving filing form logic into `shared/`.

### FH5-12

- Request: 想为所有页面都加一层新的 fetch 封装，先评估是不是值得。
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - base data access already uses `@nio-wad/hooks.fetch`
  - repo also uses page/domain-specific wrappers such as `ChargingPileApi` and `FirstOwnerGateway`
- Reviewer note: This is a strong business-side `A3` sample; the lower-cost path is to keep the current thin-wrapper pattern.

### FH5-13

- Request: 想补一套 debug 流程，让每个 brand 本地都能稳定跑起来。
- Assessed behavior: `light_clarification`
- Repo facts:
  - `scripts/load-env.js` already switches brand-specific env and project path
  - shared app utils already read brand-scoped debug account/token env vars
  - vConsole init is already wired for non-prod envs
- Reviewer note: The right trigger behavior is to ask which brand/env step is unstable before abstracting a new debug system.

### FH5-14

- Request: 品牌配置和地区配置要不要拆成两层 provider？
- Assessed behavior: `consult_challenge_trigger`
- Repo facts:
  - repo mostly injects app config through `process.config` and per-app JSON files
  - a provider-style runtime abstraction is not a prominent existing pattern in this codebase
- Reviewer note: Correct to treat as a long-term boundary decision, but the answer can get speculative too easily if it leans too hard on “provider” terminology.

### FH5-15

- Request: 把 `apps/cn/nio/README.md` 里的 `build:web` 和 `build:offline` 说明补完整。
- Assessed behavior: `direct_no_trigger`
- Repo facts:
  - this is a bounded README completion request
  - the needed sources are already in `package.json`, `offlinepkg.config.js`, and the existing README command table
- Reviewer note: Business context should not drag this out of quick-fix territory.

## Interim Calibration Notes

- Trigger boundary observations:
  - Batch 2 does not show systemic business-side over-trigger.
  - The strongest business value comes from exposing existing repo structure that makes a proposed shortcut or abstraction unnecessary.
  - `A1` remains healthiest when phrased as “先确认真实目标/现有复用面” and answered with one factual clarifier before broader challenge.
- Business-specific false positives:
  - none observed in this 15-sample review
- Business-specific false negatives:
  - none observed in this 15-sample review
- Candidate wording adjustments:
  - Add a business-facing example to `A1`: “已有现成业务流时，先确认是在扩现有流程还是新开流程”
  - Add a business-facing example to `A3`: “现有页面级 gateway / draft / shared 机制已能满足目标时，不要再加一层统一抽象”
  - Add a caution note to `A4`: avoid jumping to `provider` / “统一平台层” language when the repo still works mainly via config files and thin runtime wiring
