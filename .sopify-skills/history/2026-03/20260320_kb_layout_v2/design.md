# 技术设计: Sopify KB Layout V2（`kb-layout-v2`）

## 设计目标

在不扩张知识层级的前提下，把 `.sopify-skills` 收敛成一套可长期稳定维护、可被 runtime 体系化消费的 KB 结构：

1. 长期知识层收敛为 `project.md + blueprint/*`
2. `plan/*` 保持当前方案包定位不变
3. `history/*` 严格收口为“归档层”
4. progressive 创建时机与真实生命周期一致
5. runtime、skills、templates、README、tests 统一切到 V2

## 目录契约

### 1. 长期知识层

#### `project.md`

定位：

- 逻辑上属于长期知识层
- 物理上继续保留在 `.sopify-skills/project.md`
- 作为全局技术约定单例，不并入 `blueprint/`，避免路径迁移扩大化

只允许写：

- 技术栈与 runtime 快照
- 全局工程约定
- 测试 / 日志 / 命名 / 目录约定
- 发布 / 运行约束

禁止写：

- 长期目标与范围
- 架构分层说明
- 当前任务信息
- 长期 backlog

#### `blueprint/README.md`

只负责：

- 项目入口索引
- 托管摘要区块
- 指向 `project.md / background.md / design.md / tasks.md`
- 按当前物化状态渐进披露下一层入口

不负责：

- 长篇背景论证
- 当前任务流水
- 深层正文搬运
- 不存在文件的死链接

#### `blueprint/background.md`

只负责：

- 长期目标
- 范围内 / 范围外
- 边界、非目标

#### `blueprint/design.md`

只负责：

- 架构契约
- 宿主契约
- 目录契约
- 状态契约
- KB layout contract

#### `blueprint/tasks.md`

只负责：

- 未完成长期项
- 明确延后项

不再记录：

- 已完成里程碑流水
- 当前 plan 的任务列表

### 2. 当前工作层

#### `plan/*`

职责不变：

- 承载本轮方案
- 提供当前任务拆解
- 作为 develop 的主工作上下文

### 3. 归档层

#### `history/*`

职责固定为：

- 只读归档
- 只在显式 `~go finalize` 成功后产生
- 默认不进入规划或开发上下文

## Bootstrap Blueprint Contract

### 1. 零 plan 模式

首次安装或首次触发 Sopify，且当前工作区还没有 active plan 时，`blueprint/README.md` 必须进入零 plan 模式。

零 plan 模式下只允许写：

- 项目名
- 工作区路径或 runtime root 等稳定事实
- 已识别 manifest / 顶层目录
- 当前状态：无活动 plan、无 history
- 生命周期提示：首次进入 plan 后会补齐深层 blueprint，首次 finalize 后会生成 history

零 plan 模式下禁止写：

- 推测性的长期目标
- 范围内 / 范围外结论
- 架构边界结论
- 长期 backlog
- 历史入口链接
- 指向尚未物化文件的死链接

### 2. README 渐进式披露层级

固定四层披露：

- `L0 bootstrap`
  - 仅显示零 plan 索引与生命周期提示
- `L1 blueprint-ready`
  - 深层 blueprint 已物化，可展示 `background / design / tasks` 的入口
- `L2 plan-active`
  - 存在 active plan，可额外展示当前活动摘要与阶段
- `L3 history-ready`
  - 已存在 history，可展示最近归档与 history 入口

### 3. 共享 renderer

bootstrap、first plan、finalize 不应各自手写一套 README 文案。

抽取共享 `blueprint index renderer`，统一根据：

- 深层 blueprint 是否存在
- 当前是否有 active plan
- history 是否存在

来渲染当前层级的 README。

## blueprint 内部渐进式披露

### 固定区块

README 保持稳定的入口结构，但各区块内容按物化状态渐进显示：

1. 当前状态
2. 项目目标摘要
3. 长期知识地图
4. 当前活动
5. 深入阅读入口
6. 最近归档

### 显示规则

- 深层 blueprint 不存在时：
  - 只显示“首次进入 plan 生命周期后生成”
- 无 active plan 时：
  - 只显示“当前无活动 plan”
- history 不存在时：
  - 只显示“首次 finalize 后生成”
- README 永远只做入口索引，不展开深层正文

## progressive 生命周期

### Stage A: 首次触发

只创建：

- `.sopify-skills/blueprint/README.md`
- `.sopify-skills/project.md`
- `.sopify-skills/user/preferences.md`

此时 `README.md` 处于 `L0 bootstrap`。

### Stage B: 首次进入 plan 生命周期

补齐：

- `.sopify-skills/blueprint/background.md`
- `.sopify-skills/blueprint/design.md`
- `.sopify-skills/blueprint/tasks.md`
- `.sopify-skills/plan/<plan-id>/...`

同时必须：

- 在深层 blueprint 物化后立刻通过共享 renderer 刷新 `blueprint/README.md`
- 当 active plan 已创建时，把 README 提升到 `L2 plan-active`
- 若只是提前补齐 deep blueprint 但尚无 active plan，则停留在 `L1 blueprint-ready`

此时 `README.md` 升级到 `L1` 或 `L2`。

### Stage C: 首次成功 finalize

创建：

- `.sopify-skills/history/index.md`
- `.sopify-skills/history/YYYY-MM/<plan-id>/...`

此时 `README.md` 升级到 `L3`。

### 配置覆盖: `kb_init: full`

V2 下保留 `full`，但重新定义为“显式提前物化更多长期文档”，而不是回到旧结构：

- 允许提前创建 `blueprint/background.md`、`blueprint/design.md`、`blueprint/tasks.md`
- 允许提前创建 `user/feedback.jsonl`
- 不允许再创建 `wiki/*`
- 不允许预建 `history/*`
- README 仍必须走共享 renderer；若尚无 active plan，则最高只到 `L1 blueprint-ready`

## 文档消费契约

### 1. manifest 最小扩展

manifest 新增：

```json
{
  "kb_layout_version": "2",
  "knowledge_paths": {
    "project": ".sopify-skills/project.md",
    "blueprint_index": ".sopify-skills/blueprint/README.md",
    "blueprint_background": ".sopify-skills/blueprint/background.md",
    "blueprint_design": ".sopify-skills/blueprint/design.md",
    "blueprint_tasks": ".sopify-skills/blueprint/tasks.md",
    "plan_root": ".sopify-skills/plan",
    "history_root": ".sopify-skills/history"
  },
  "context_profiles": {
    "consult": ["project", "blueprint_index"],
    "plan": ["project", "blueprint_index", "blueprint_background", "blueprint_design"],
    "clarification": ["project", "blueprint_index", "blueprint_tasks"],
    "decision": ["project", "blueprint_design", "active_plan"],
    "develop": ["active_plan", "project", "blueprint_design"],
    "finalize": ["active_plan", "project", "blueprint_index", "blueprint_background", "blueprint_design", "blueprint_tasks"],
    "history_lookup": ["history_root"]
  }
}
```

### 2. knowledge resolver

新增统一 resolver，负责：

1. 解析 V2 长期知识路径
2. 基于 `context_profiles` 选择当前 route 要读哪些文件
3. 隔离 runtime 对具体目录结构的耦合
4. 在 progressive 生命周期下返回“当前存在的文件集合”，而不是要求调用方自行判断缺文件
5. 暴露当前 `materialization_stage`，让 tests 与 host 都能判断当前处于 `L0/L1/L2/L3` 哪一层
6. 让 tests 可直接断言 profile 与上下文选择

### 3. 默认消费规则

- `consult`：只读 `project.md + blueprint/README.md`
- `plan`：读 `project.md + blueprint/README.md + background.md + design.md`
- `clarification`：读 `project.md + blueprint/README.md + blueprint/tasks.md`
- `decision`：读 `project.md + blueprint/design.md + active plan`
- `develop`：以 active `plan/*` 为主，必要时补 `project.md + blueprint/design.md`
- `finalize`：读 active plan 与长期知识文件，做同步检查
- `history_lookup`：仅在显式查历史或回放时进入

说明：

- 默认 `consult` profile 依赖 `README` 的渐进式披露能力，不应默认拉取全部深层 blueprint
- 只有进入 `plan / decision / finalize` 等 profile 时，resolver 才进一步读取深层 blueprint
- `context_profiles` 表达的是“目标文件集合”，resolver 实际返回的是“当前 stage 下存在且允许读取的文件集合”
- `clarification`、`consult` 等早期路由在 `L0 bootstrap` 下必须 fail-open，不因 `blueprint/tasks.md` 尚未物化而报错

## 文档同步契约

### 1. 最小 `knowledge_sync` contract

替代仅有的粗粒度 `blueprint_obligation`，在 plan 元数据中引入最小矩阵：

```yaml
knowledge_sync:
  project: skip|review|required
  background: skip|review|required
  design: skip|review|required
  tasks: skip|review|required
```

V2 落地后：

- `knowledge_sync` 成为唯一正式同步契约
- 新生成 plan 不再把 `blueprint_obligation` 作为 canonical 字段
- 若 loader 读到旧 `blueprint_obligation`，只用于 legacy reject 或短期兼容投影，不再作为新实现的判断依据

### 2. 含义

- `skip`：本轮无需同步该文件
- `review`：本轮可能影响该文件，finalize 时至少复核
- `required`：本轮必须更新该文件，否则 finalize 阻断

### 3. 默认映射

- `light`
  - `project: skip`
  - `background: skip`
  - `design: review`
  - `tasks: skip`

- `standard`
  - `project: review`
  - `background: review`
  - `design: review`
  - `tasks: review`

- `full`
  - `project: review`
  - `background: required`
  - `design: required`
  - `tasks: review`

### 4. finalize 行为

finalize 固定执行：

1. 归档 active plan 到 history
2. 刷新 `blueprint/README.md`
3. 按 `knowledge_sync` 检查长期文档是否需要复核或必须更新
4. 写入 / 更新 `history/index.md`
5. 清理 active state
6. 按共享 renderer 刷新 `blueprint/README.md` 当前披露层级

明确禁止：

- 不把 plan 全文抄入 blueprint
- 不把 history 回灌为长期正文
- 不让 history 成为默认长期上下文

## 输出评分契约

后续所有正式 plan 包统一附带：

```md
评分:
- 方案质量: X/10
- 落地就绪: Y/10

评分理由:
- 优点: 1 行
- 扣分: 1 行
```

评分维度固定内部使用：

1. 精简性
2. 稳定性
3. 定义明确度
4. 体系化消费能力
5. 实施可控性

## 实施顺序

1. 先切 V2 目录契约与 bootstrap 时机
2. 再落 `Bootstrap Blueprint Contract` 与共享 README renderer
3. 再落 manifest 扩展与 stage-aware knowledge resolver
4. 再切 `knowledge_sync` 并清理 `blueprint_obligation` 的旧消费点
5. 最后统一 README、blueprint、skills、templates 与 tests 口径

## 设计结论

V2 第一版只做必要结构收敛，不引入新的模块层，也不保留默认兼容双轨。核心原则是：

1. 知识层更少
2. 生命周期更真
3. 入口索引渐进披露
4. 消费入口统一
5. 同步规则可机器检查
6. 文档与 runtime 使用同一套世界观
7. `blueprint/README.md` 是纯索引页，只保留入口与状态，不承载长篇说明
8. `L0/L1/L2/L3`、共享 renderer、manifest V2 knowledge contract 与 `knowledge_sync` 在本轮即视为正式 contract
