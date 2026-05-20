# 技术设计: P6 Canonical Writer Cutover

## 范围边界

**在范围内**：StateStore 物理提取 + writer_input 契约定义 + runtime 消费者重接线。

**不在范围内**：
- Validator 物理提取（P5 已标位置，留后续）
- Copilot 外部 repo 接入（独立证据候选 Copilot Payload-Only Onboarding Proof）
- protocol.md 修改（writer_input 成熟后再协议化）
- 新 CLI 命令或用户面变更

## 技术方案

### 总体策略

"Strangler fig without migration"——无用户，直接切出新栈，runtime 原地退为 legacy。

```
当前:  engine → StateStore(state.py 内部类) → state/*.json
目标:  engine → canonical_writer(独立模块) → state/*.json
       新宿主 → canonical_writer → state/*.json
       runtime = legacy reference, 消费 canonical_writer
```

### 提取目标分析

**StateStore 类**（runtime/state.py:40-315, 类整体 ~276 LOC，candidate-kernel ~210 LOC）

核心方法族（6 domain × get/set/clear = 18+ 方法）：

| domain | get | set | clear | invariants |
|--------|-----|-----|-------|-----------|
| current_run | ✅ | ✅ phase_validate | ✅ | resolution_id stamp |
| last_route | ✅ | ✅ | — | json serialization |
| current_plan | ✅ | ✅ | ✅ | — |
| current_clarification | ✅ | ✅ phase_validate+resume | ✅ | provenance stamp |
| current_decision | ✅ | ✅ phase_validate+resume | ✅ | provenance stamp |
| current_handoff | ✅ | ✅ | ✅ | observability meta |
| current_archive_receipt | ✅ | ✅ | ✅ | observability meta |
| host_facing_truth | — | ✅ compound | — | paired write + resolution_id |

**必须随迁的辅助**：

| 辅助 | 来源 | LOC (估) | 说明 |
|------|------|----------|------|
| state_invariants.py | 独立文件 | ~100 | validate_phase, validate_resolution_id, validate_paired_host_truth_write, stamp_* |
| _read_json / _write_json | state.py 内 | ~15 | atomic JSON 持久化 |
| iso_now | state.py 内 | ~3 | UTC timestamp |
| normalize_session_id | state.py 内 | ~12 | session_id 校验 |
| _stamp_*_provenance | state.py 内 | ~20 | clarification/decision provenance |
| _validate_state_resume_contract | state.py 内 | ~20 | checkpoint resume 校验 |

**不随迁（留 runtime）**：
- read_runtime_handoff（handoff.py）— StateStore.get_current_handoff 调用，但属消费逻辑
- models.py 类型定义 — 已是 cross-tier，保持原位

**checkpoint_request 边界决策**：

StateStore 仅使用 `CheckpointRequestError`（异常类）和 `validate_develop_resume_context()`（~35 LOC 校验函数），用于 `_validate_state_resume_contract()` 中的 develop checkpoint resume 校验。

checkpoint_request.py 本身（390 LOC）不是无依赖的——它 import `runtime.clarification` 和 `runtime.models`。因此不能整体迁入 canonical_writer/。

**处置**：将 StateStore 使用的 2 个符号（`CheckpointRequestError` + `validate_develop_resume_context`）提取到 canonical_writer/（~37 LOC），canonical_writer 不引用 checkpoint_request.py 整体。checkpoint_request.py 本体留 runtime，其余消费者不受影响。这保证 canonical_writer/ 无 runtime 回指。

### S1: writer_input 契约规格

定义 canonical writer 的对外接口：

1. **WriterInput 类型族**：每个 set 方法的入参即一个 writer_input。不引入新的通用容器——保持现有强类型签名
2. **Invariant 契约**：哪些校验是 writer 自己做的 vs caller 负责的
3. **IO 契约**：文件路径 convention、atomic write 语义、JSON 编码约定
4. **Observability 契约**：writer stamp（writer="canonical_writer"）、timestamp、provenance

输出：`writer_input_contract.md`

### S2: 物理提取

创建独立模块，从 state.py 提取 StateStore：

**方案 A（推荐）：新顶层模块 `canonical_writer/`**
```
canonical_writer/
  __init__.py          # re-export StateStore
  store.py             # StateStore 类 + IO helpers
  invariants.py        # 从 state_invariants.py 迁移
  _time.py             # iso_now (dedup 5 处重复)
```

**方案 B：runtime 内部重组 `runtime/writer/`**
```
runtime/writer/
  __init__.py
  store.py
  invariants.py
```

方案 A 强调 canonical writer 是新的独立层（不属于 runtime）。方案 B 降低初始风险但退场不彻底。

**选择标准**：蓝图三层分离定位 → canonical writer 不是 runtime 的子模块 → 方案 A。

### S3: 消费者重接线

runtime 内 ~15 个文件导入 StateStore，需逐个改为从新模块导入。

| 消费者分类 | 文件数 | 策略 |
|-----------|--------|------|
| runtime 核心（engine, gate, bridges） | ~10 | import 路径切换，行为不变 |
| installer（inspection.py） | 1 | import 路径切换 |
| scripts（sopify_runtime.py, skill-eval） | 2 | import 路径切换 |
| tests | ~5 | import 路径切换 + fixture 不变 |

**兼容性桥接（临时迁移桥，非长期设计）**：在 `runtime/state.py` 保留 `from canonical_writer import StateStore` re-export，标 deprecated。目标是 S4 阶段清除所有旧路径引用后移除桥接，避免双归属。

### S4: 验证 + 清理

1. 721+ tests 全过（零行为变更）
2. iso_now 重复清理：5 处 → 统一从 `canonical_writer/_time.py` 导入
3. state.py 瘦身：只保留 re-export + deprecated 标记
4. 确认 canonical_writer/ 无 engine 依赖（import 审计）

## 风险

| 风险 | 等级 | 缓解 |
|------|------|------|
| 提取后循环导入 | 中 | S2 先画完整 import graph，确认新模块无回指 runtime |
| invariant 遗漏 | 中 | S1 逐方法列 invariant，S4 用现有测试覆盖验证 |
| 消费者遗漏 | 低 | grep 全量扫描，CI 兜底 |
| 新宿主适配性 | 低-中 | writer_input contract 由 S1 文档化，但真实适配需后续宿主试点验证 |
