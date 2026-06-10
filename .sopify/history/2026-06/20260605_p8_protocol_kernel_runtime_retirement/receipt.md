---
plan_id: 20260605_p8_protocol_kernel_runtime_retirement
outcome: completed
completed_at: 2026-06-10
waves: Phase 0 + W3.1 + W3.2 + W3.3 + W3.4 + W3.5 + W3.6
---

# P8 Protocol Kernel & Runtime Retirement — Final Receipt

## Summary

P8 将 Sopify 的真相源从 runtime 切换到 protocol kernel。Runtime 物理删除（46 files / ~15.6K LOC），canonical root 从 `.sopify-skills` 重命名为 `.sopify`，state model 从 6 文件收窄到 2 文件（active_plan + current_handoff）。Qoder 作为首个 PROTOCOL_VERIFIED 宿主通过端到端 proof transcript 验证了无 runtime 接续能力。产品定位确定为"开发过程协议层"，蓝图/README/架构图全部对齐到 post-P8 叙事。

## Wave Status

| Wave | Scope | Status |
|------|-------|--------|
| Phase 0 | Pre-flight cleanup (stale state, dead governance chain, project.md) | ✅ |
| W3.1 | Qoder PROTOCOL_VERIFIED host adapter | ✅ |
| W3.2 | Installed payload writer proof | ✅ |
| W3.3 | End-to-end proof transcript (Session A→B→Finalize) | ✅ |
| W3.4 | Canonical root rename `.sopify-skills` → `.sopify` | ✅ |
| W3.5 | Docs narrative cutover (README, how-sopify-works, architecture SVG) | ✅ |
| W3.6 | Blueprint sync (design.md, protocol.md, ADR-013/017, tasks.md) | ✅ |
| Wave 3 Gate | All verification criteria passed | ✅ |

## Key Metrics

| Metric | Value |
|--------|-------|
| Files changed (total across all commits) | ~200+ |
| LOC deleted | ~31,000+ (runtime + tests + legacy) |
| LOC added | ~3,500+ (protocol kernel + proof + docs) |
| Net LOC reduction | ~27,500 |
| Test count | 181 passed, 26 subtests passed |
| Protocol smoke | 3/3 PASS (new-plan / continuation / finalize) |
| Host adapters | 4 (Codex, Claude, Qoder = PROTOCOL_VERIFIED; Copilot = BASELINE_SUPPORTED) |

## Key Decisions

- **Runtime physically deleted** (W2.10): 46 files / ~15.6K LOC removed; protocol kernel is sole truth source
- **Canonical root fixed to `.sopify`** (W3.4): 481 replacements across all layers; `plan.directory` configurable root removed
- **State model 6→2 files** (W2.4-W2.5): `active_plan.json` + `current_handoff.json` only; all other state files retired
- **Qoder PROTOCOL_VERIFIED** (W3.1-W3.3): home-scope hybrid adapter, bare `--target qoder` via `default_language`, end-to-end proof transcript
- **Product positioning**: "开发过程协议层" — 用户层(能停能接能查) / 产品层(协议层) / 能力层(接续留痕审计) / 架构层(protocol kernel + workflow + adapters)
- **EAR/gate_receipt retired**: pre-execution authorization model replaced by post-execution evidence chain (receipts + history receipt)
- **Validator → protocol admission**: sopify_writer does structural validation; host prompt does semantic guidance
- **Host capability tiers redefined**: convention_only / payload_capable / protocol_verified (deep_verified retired)

## Commit Chain

```
13ee4b2 w3.6: blueprint sync — post-P8 narrative alignment
b177e10 fix: rename missed test fixtures
6a8560e w3.5: docs narrative cutover
3f97d80 w3.4: canonical protocol root .sopify
a5f6c06 w3.2+w3.3: Qoder proof package
2933cd6 w3.1: Qoder PROTOCOL_VERIFIED host adapter
95b3880 phase-0: pre-flight cleanup
```

## Follow-ups (Recorded)

- **Protocol prose cleanup**: post-P8 active wording normalization in protocol.md — recorded in `.sopify/blueprint/tasks.md`
- **Copilot Workspace Protocol Uplift** (W4.0): upgrade from BASELINE_SUPPORTED to WORKSPACE_PROTOCOL_VERIFIED — recorded as P8 Extension Candidate
