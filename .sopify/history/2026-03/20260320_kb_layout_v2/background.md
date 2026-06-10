# 变更提案: Sopify KB Layout V2（`kb-layout-v2`）

## 需求背景

当前 `.sopify-skills` 的知识结构已经出现两类问题：

1. 长期知识层同时存在 `blueprint/` 与 `wiki/` 两套根，职责重叠。
2. runtime 已经把 `blueprint` 当成长期契约层使用，但 skills / templates / README / tests 仍保留旧知识库口径。
3. `history/index.md` 和 `wiki/overview.md` 在 bootstrap 阶段就被创建，渐进式创建不够纯粹。
4. 文档存在，但缺少统一的机器消费契约，容易退化为“仅供人工阅读的说明文档”。
5. 首次安装或首次触发 Sopify 时通常还没有 active plan，`blueprint/README.md` 若没有零 plan 模式约束，容易在 bootstrap 阶段写出推测性目标、死链接或伪规划内容。
6. `kb_init: full` 仍沿用旧世界，继续预建 `wiki/*` 与 `history/index.md`，如果不一起重定义，会让 V2 在显式配置场景下继续漏回旧结构。

当前已确认的方向是：

1. 保留 `plan/` 作为高频方案包工作区。
2. 把 `blueprint/` 收敛成唯一长期知识根。
3. 将 `project.md` 纳入长期知识层，但避免与 `blueprint/*` 职责重复。
4. 将 `history/` 严格定义为“显式收口后才产生的归档层”。
5. 不引入 `blueprint/modules/*`，避免增加暂时无人稳定消费的新层级。
6. 一次性切断 `wiki/*` 与 `blueprint_obligation` 的旧口径，不保留默认兼容双轨。
7. `blueprint/README.md` 收缩为纯索引页，只允许保留索引级简单描述，不承载长篇说明。
8. `L0/L1/L2/L3` 渐进披露、共享 `blueprint index renderer`、manifest V2 knowledge contract 与 `knowledge_sync` 全部冻结为正式 contract，不再以“建议”处理。

## 本轮目标

### 1. 收敛 V2 目录契约

- 长期知识层只保留 `project.md + blueprint/*`
- `wiki/overview.md` 退役
- `history/` 延迟到首次 `~go finalize` 再真实生成

### 2. 把渐进式创建做实

- 首次触发只创建最小骨架
- 首次 plan 才补齐深层 blueprint
- 首次 finalize 才创建 history

### 3. 让 blueprint 内部也支持渐进式披露

- `blueprint/README.md` 永远是项目入口索引，而不是长篇总说明
- README 根据当前物化状态分层披露入口
- 首次安装且无 plan 时进入零 plan 模式，只暴露可验证事实

### 4. 让文档进入体系化消费

- 通过 manifest 明确 V2 knowledge contract
- 通过统一 resolver 约束 runtime 读取哪些长期文档
- 禁止继续散落硬编码路径

### 5. 稳定 plan -> blueprint -> history 的联动

- plan 负责本轮实施
- finalize 根据同步契约决定哪些长期文件需要复核或更新
- history 只承接归档，不回灌为长期正文

## 方案评分

- 方案质量: 9.8/10
- 落地就绪: 9.4/10

评分理由：

- 优点: 目录、生命周期、消费契约、同步契约与 bootstrap 索引契约已经一起收口，且“不兼容双轨、README 纯索引、关键 contract 直接冻结”为实现阶段消除了主要摇摆空间。
- 扣分: resolver、README renderer、manifest 扩展与 `knowledge_sync` 仍未落成代码与测试，当前提升的是方案确定性，不是实现完成度。

## 范围

### 范围内

- `.sopify-skills` V2 目录契约
- KB bootstrap 的最小骨架调整
- Bootstrap Blueprint Contract
- blueprint 内部渐进式披露
- blueprint 四件套职责收敛
- history 延迟创建
- knowledge manifest contract
- knowledge resolver
- finalize 的最小同步契约
- skills / templates / README / tests 的统一切口

### 范围外

- 不引入 `blueprint/modules/*`
- 不保留 `wiki/*` 的默认兼容双轨
- 不让 `history/*` 进入默认规划或开发上下文
- 不重做现有 route / handoff / execution gate 状态机
- 不在本轮引入新的长期知识目录

## 目标结构

```text
.sopify-skills/
├── blueprint/
│   ├── README.md
│   ├── background.md
│   ├── design.md
│   └── tasks.md
├── project.md
├── user/
│   ├── preferences.md
│   └── feedback.jsonl
├── plan/
│   └── YYYYMMDD_feature/
├── history/
│   ├── index.md
│   └── YYYY-MM/
├── state/
└── replay/
```

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 旧路径硬编码残留在 runtime 中 | V2 结构落地后仍会读写旧文件 | 用统一 knowledge resolver 替代散落路径判断，并以测试兜底 |
| `project.md` 与 `blueprint/*` 职责继续膨胀重叠 | 长期知识层再次失焦 | 固定每个文件的允许职责与禁止职责，并同步模板 |
| `history` 延迟创建影响现有默认假设 | bootstrap / README / tests 行为变化较大 | 将 history 调整列为独立切片，连同 tests 一次收口 |
| finalize 只做归档不做同步，长期文档继续漂移 | 文档与代码脱节 | 补最小 `knowledge_sync` contract，并在 finalize 时检查 |
| bootstrap 阶段的 README 写入推测性内容 | 首次安装即产生错误长期认知 | 将 blueprint 首次生成限制为“零 plan 索引模式”，只写可验证事实，并禁止死链接 |
| `kb_init: full` 仍预建旧文件 | 用户显式开 full 仍会回到旧结构 | 在 V2 中重定义 full：允许提前物化 deep blueprint，但不允许预建 `wiki/*` 或 `history/*` |

## 成功标准

1. 新工作区首次触发后只创建 `blueprint/README.md`、`project.md`、`user/preferences.md`。
2. 首次进入 plan 生命周期后，才补齐 `blueprint/background.md / design.md / tasks.md`。
3. 首次成功 `~go finalize` 前，工作区中不存在真实 `history/index.md`。
4. runtime 的长期知识读取统一通过 manifest + resolver 获取，不再默认读取 `wiki/*`。
5. `project.md`、`blueprint/*` 的职责边界在模板、README、skills、tests 中完全一致。
6. 首次安装且无 plan 时，`blueprint/README.md` 只输出零 plan 索引，不包含推测性目标、死链接或深层正文。
7. `blueprint/README.md` 在 bootstrap / first plan / first finalize 三个阶段遵守同一套渐进式披露规则。
8. plan 包输出固定附带“方案质量 / 落地就绪”评分区块。
