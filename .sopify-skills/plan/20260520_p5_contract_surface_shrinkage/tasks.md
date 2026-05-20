---
plan_id: 20260520_p5_contract_surface_shrinkage
feature_key: p5_contract_surface_shrinkage
level: standard
lifecycle_state: active
---

# 任务清单

## S1: Deep-Only Surface 全量清点 ✅

- [x] Runtime 模块级扫描：标注每个模块的外部消费者类型（deep_verified / cross-tier / internal）
- [x] Installer 面清点：HostAdapter, payload bundle, SupportTier 映射
- [x] Manifest/Bridge 面清点：FeatureId, capability projection, bridge capability
- [x] Output 渲染面清点：deep-only 渲染逻辑 vs 通用渲染
- [x] 输出 `surface_inventory.md`（两轮：模块级 + 行级 sub-surface 拆分）

## S2: 证据依赖消费

> P5 消费以下证据型候选的结论，不拥有其执行。

### 依赖 1: Shadow Writer Gap Analysis ✅

- [x] P5 内部产出分析（无外部证据生产者）→ `shadow_writer_analysis.md`
- [x] 消费结论 B（部分可行）：builder 不可行，StateStore 部分可行
- [x] 映射到 S3 裁定表：candidate-kernel 从 5 面 ~680 LOC → 1 面 ~210 LOC
- [x] canonical writer authority 轴结论：当前不需要独立建模

### 依赖 2: Copilot Payload-Only Onboarding Proof

- [ ] 确认证据已就绪（或标记为 pending，先出 provisional 裁定）
- [ ] 消费 onboarding 可行性结论 + 卡点清单，映射到 S3 裁定表

## S3: 裁定表 ✅ (final — Shadow Writer applied)

- [x] 消费 S1 产出，生成 provisional 裁定表（58 面 × 4-way 裁定 × evidence_status）→ `provisional_adjudication.md`
- [x] 消费 S2.1 Shadow Writer 结论 B，升级为 final 裁定表
- [x] 确定最小必留面清单：candidate-kernel = 1 面 ~210 LOC (StateStore)
- [x] 用户确认 final 裁定表
- [ ] Onboarding Proof 就绪后更新 3 个 pending-onboarding 面（不挡 S4 主线）

## S4: 执行裁定

- [ ] 低风险项执行（明确 deep-only 的标记/降级/删除）
- [ ] 高风险项执行（需 shadow writer 结论支撑的面）
- [ ] 执行后测试套件回归验证
- [ ] design.md / protocol.md 同步更新（如有 contract 面变更）

## S5: 结论报告

- [ ] 标准 receipt 格式
- [ ] 裁定表执行结果
- [ ] 最小必留面清单（P6 输入）
- [ ] LOC 变化量统计
- [ ] 归档至 history/

## 决策记录

### DR-1: Shadow Writer Gap Analysis 结论

- **决策**: 结论 B（部分可行）
- **日期**: 2025-05-20
- **影响**: candidate-kernel 从 ~680 LOC 缩至 ~210 LOC (仅 StateStore)
- **详见**: `shadow_writer_analysis.md`
- **4 面降级**: build_runtime_handoff, write_runtime_handoff, decision build_*, clarification build → keep-deep-only
- **1 面保持**: StateStore get/set/clear → keep-candidate-kernel

### DR-2: Canonical Writer Authority 轴

- **决策**: 当前不需要独立建模为正交轴
- **日期**: 2025-05-20
- **理由**: 非 deep host 核心需求是读取非写入；writer authority 本质是 "哪个 engine" 而非 "谁被授权"；protocol + Validator 可覆盖
