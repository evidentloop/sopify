# Archive Receipt: 20260529_pre_launch_consolidation

## Metadata

- **plan_id**: 20260529_pre_launch_consolidation
- **level**: standard
- **created**: 2026-05-29
- **archived**: 2026-06-05
- **outcome**: partial_done（主航道完成；部分 Wave 明确 defer）

## Summary

推广前收口整合包，覆盖 D1 README 重写 / D3 命令面收敛 / D5-3B 安全修复 / Wave A 首次触达 / Wave B 文档打磨 / Wave C 输出增强 / Wave D 推广文章 / Wave E 延后项。

主航道（D1 / D3 / D5-3B / Wave A / Wave B / Wave C）已完成；代码和文档能对上，PR #54 output-contract enforcement 是 Wave C 的硬证据。

Wave D（推广文章）草稿就绪（掘金 / V2EX / dev.to / X / 小红书），本地位于 `docs/articles/`（`.gitignore` 忽略，不进入可审计归档资产）；归档日用户决定删除该目录，发布时再单独处理。

Wave E 中 runtime 线（7.1–7.4）已被 **P8 Protocol Kernel & Runtime Retirement** 吸收；手工项 / 推广后项明确 defer。

## Key Decisions

1. **docs/articles 不归档**：草稿质量与可审计资产标准不符；`.gitignore` 忽略状态保留。归档日用户决定删除该目录。
2. **runtime 线迁到 P8**：installer 解耦 / runtime 降级等原 Wave E 任务不再在本包推进，挂 P8 Wave 3。
3. **skill-standards-refactor.md 保留为 dormant**：顶部加 `status: deferred`，蓝图 README 仍引用，后续再评估。
4. **不扩展本包**：P8 已是新的架构主线（Protocol Kernel & Runtime Retirement），pre_launch 不应再吸收新任务。

## Wave Status at Archive

| Wave | 状态 | 备注 |
|---|---|---|
| D1 README 重写 | ✅ done | |
| D3 命令面收敛 | ✅ done | |
| D5-3B 安全修复 | ✅ done | |
| Wave A 首次触达 | ✅ done | |
| Wave B 文档打磨 | ✅ done | |
| Wave C 输出增强 | ✅ done（PR #54） | tasks.md 状态回写 |
| Wave D 推广文章 | drafts prepared | 草稿本地就绪；发布 deferred |
| Wave E 延后项 | absorbed / deferred | runtime 线迁 P8；手工项 defer |

## Verification Evidence

- PR #54 output-contract enforcement（Wave C 硬证据）
- 656+ tests pass（归档日基线；未在本归档流程中复跑）
- README / README.zh-CN / docs/how-sopify-works 已对齐当前行为

## Follow-ups（不阻断归档）

- 用户发布推广稿时再单独处理（可能新开 plan 包或直接发布）
- skill-standards-refactor.md 后续评估（P8 / P9 之前或期间）
- GitHub repo metadata / cover 图 / Discord / Discussions 等有真实用户后再开
- Registry 不活跃条目清理（独立工具项）
