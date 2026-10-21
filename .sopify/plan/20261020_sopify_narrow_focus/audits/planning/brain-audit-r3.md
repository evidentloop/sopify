# Sopify 整体审计裁决（R3）与通往统一方案包的步骤

依据：codex-r3.md（pstack 代码深读 + 价值证据，统计见 r3-stats.json）、gemini-r3.md（市场侧 + 验收清单），以及 R1/R2 四份报告。基线 main@9d9b319。本轮没有改动仓库。

## 一、价值审计结论：收窄（两边一致）

**定位**：Sopify 从「教 AI 先想再写的工作流」收窄为「跨宿主可携带的方案与证据契约」。

| 承诺 | 证据 | 裁决 |
|---|---|---|
| 先问再写 | 至少 7 个归档包记录了真实的停车和用户裁定。但四个宿主（Claude Code、Codex、Cursor、Antigravity）都已原生提供 plan mode，而 Sopify 这一项主要靠 prompt 约束 | 降级为基础能力，不再当差异化卖点 |
| 决策留痕 | 最近 6 个归档包全部有回执（verify 5/6，final 6/6）。writer 在代码层面保证了方案版本绑定和回执不被覆盖 | **保留并强化**：这是代码真正兜底的部分 |
| 跨宿主续做 | 有跨宿主审查和返修的真实链条（Cursor 方案；CLI entry 中 Codex 执行、Cursor 审查，带真实 Orca Dispatch ID）。但**归档里找不到一条由两个不同执行会话真正冷启动接续的链**：Qoder proof 是模拟，Copilot pilot 是构造 fixture | 这是最想守的差异，却也是证据最薄的一项。**新方案包必须补一次真实验证** |

成本数据：
- 每个宿主入口规则约 10.5KB，粗估 2.6k–5.3k token；Copilot 平铺成单文件后约 42KB。
- 近 6 个月提交里，26%–34% 与宿主适配相关，宿主维护面是主要负担。
- 核心代码不大：contracts 1.5k 行、writer 0.6k 行。

### 对验收官结论的纠偏
- 「跨宿主续做是最不可撼动的护城河」：这是意图，还不是事实。是否成立，以方案包里的冷启动样本（T9）结果为准。
- 「receipt 防篡改」：不成立。writer 只做到原子独占创建，provenance 由调用方自己填写；绕过 writer 直接改文件不会被拦住。
- Antigravity 验收「只做 dry-run」：证据不够，必须在真实 agy 会话里确认 skills 和规则确实被加载。
- Trae「`.trae/rules/sopify.md`」：这个路径还没有实际加载的证据，属于待验证项。

## 二、pstack 借鉴：只并入现有三处，不新增产品线

| 借鉴 | 并入 | 不学 |
|---|---|---|
| bug 配方（同一表面复现 → 假设 → 修复 → 同一复现通过）、修前失败与修后通过的证据 | T2 修复验收、develop 规则的小分支 | 23 个 playbook、56 个 Skill、个人化命名 |
| 验证账本绑定代码 SHA、标明证据级别（proof level） | T3 的 findings / task packet，复用现有 evidence 字段 | orch.ts、锁、frontier、第二套 inbox |
| 多宿主共用一份源 + 能力映射 + drift 检查 | T4 宿主接入 recipe（对应 #55） | 移植它的整棵生成器包装 |
| 会话接续时核对实际 diff 和需要重新验证的项 | T3 task packet 的「继承证据 / 待重验」字段 | 默认读 transcript、暂停时自动 WIP commit |

## 三、方案包验收的全局门槛（合并双方意见）

1. writer 和 contracts 的 schema 不改，新增字段一律走 evidence。
2. 不引入常驻进程、调度器或文件锁，坚持 P8 时已确定的「Runtime 退场」原则。
3. 新宿主一律标 BASELINE_SUPPORTED，安装成功不等于协议认证。
4. 只有 plan owner 写 machine truth 和 receipt；worker_done 不等于 verify pass；不做双向进度同步。
5. README 只描述已经验证的能力，宿主支持表在适配落地后才更新。
6. 对现有用户文件（GEMINI.md、AGENTS.md、hooks、MCP 配置）只用 managed block 方式写入，不整份覆盖。

## 四、通往统一方案包的步骤

| 步 | 动作 | 谁 | 产出 / 关口 |
|---|---|---|---|
| 0 | 处理旧 active plan `20260819_cursor_support`：状态已是 completed / ready_to_archive，handoff 已 59 天没更新。建议先 `~go finalize` 归档 | 你拍板 → 大脑执行 | 旧包进 history，active 指针清空 |
| 1 | 需求分析：把本轮裁决固化为目标、范围、不做清单和评分 | 大脑 | 需求分析 ✓ |
| 2 | 方案设计：standard 级方案包 `.sopify/plan/20261020_sopify_narrow_focus/`（background / design / tasks），按下面 5 个波次、10 个任务拆分 | 大脑 | 方案包草稿 |
| 3 | 方案评审：验收官按第三节门槛和 gemini-r3 的分项 DoD 逐条验收；Codex 审可执行性（文件边界、依赖、工时） | 派发 | 两份评审意见 |
| 4 | 修订后交你确认 | 大脑 → 你 | **方案包定稿（目标达成）** |
| 5 | 之后才执行：按波次派 Codex 执行、验收官验收，大脑经 sopify_writer 写回执；每个波次结束停一次给你看 | — | — |

### 方案包内的任务结构（预览）

- **W1 可靠性**
  - T1：CI 改为跑全部测试
  - T2：修 AUDIT-1..4 和共同安装器的完整性判断；吸收 PR #75 的测试并去掉 xfail；附上修前失败、修后通过的证据
- **W2 契约与模板**（可并行）
  - T3：Sopify × Orca 执行适配（docs 加 skill）、findings 和 task packet 模板、陈旧 handoff 检查
  - T4：宿主接入 recipe，对应 #55，包括能力矩阵、负向边界、drift 检查
  - T5：develop 规则加 bug 调查分支；EARS 和 Delta Spec 作为可选模板
  - T6：README 第一阶段调整（Quick Start 前移，Architecture 和 EvidentLoop 细节挪到 docs，价值边界文案）
- **W3 宿主证明**（两项并行）
  - T7：Antigravity baseline，用验收官标签做真实加载验证
  - T8：Trae 2.x baseline
- **W4 价值证明**
  - T9：冷启动跨宿主续做样本。owner A 开出 pending task，另一个宿主上的执行者 B 只靠 `.sopify/` 文件接手，完成真实修改和验收，再由 owner 写回。记录两个执行身份、起止 SHA、方案版本
- **W5 交付**
  - T10：README 第二阶段（宿主支持表、Orca 小节），全量回归，交付 PR
