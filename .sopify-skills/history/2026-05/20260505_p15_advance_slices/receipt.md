# Receipt: P1.5 先行切片

outcome: passed
date: 2026-05-05

## Summary

P1.5 先行切片三项全部完成并合入 main（PR #22, commit 6238e9c）。Convention 入口兑现、Protocol Compliance Suite Phase 1 建立、~summary surface 全链路删除。

## Key Decisions

1. Convention 入口放在 README Quick Start 内部作为子段落，不单独建章节（D1）
2. Protocol Compliance Suite 使用 pytest + tmp_path fixture，不依赖 runtime（D4/D5）
3. `_models/summary.py` 全部 16 个 class 均为 daily_summary 专属，整文件删除（D9 结论）

## Deliverables

| 切片 | 范围 | 验收 |
|------|------|------|
| Convention 入口兑现 | README.md + README.zh-CN.md 增加 Convention Mode 段落 | 链接测试通过 |
| Protocol Compliance Suite Phase 1 | `tests/protocol/test_convention_compliance.py` 16 项断言 | 全部通过，不 import runtime |
| ~summary surface 删除 | daily_summary 全链路删除 | 595 tests passed + 6 组 grep 零残留 + 净删 2,207 行 |

## Impact on Blueprint

- tasks.md: 先行切片三项标记 ✅（Convention 入口、Compliance Suite、~summary 预清理）
- design.md: 无变更
- protocol.md: 无变更
