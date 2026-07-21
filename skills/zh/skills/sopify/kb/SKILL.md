---
name: kb
description: 管理 `.sopify/` 长期知识；负责初始化、渐进物化、读取、保留和 knowledge_sync 政策。
---

# 知识库管理

KB 负责长期知识，不替 Analyze、Design 或 Develop 做阶段判断，也不直接管理活动方案、handoff、receipt 或 finalize。文档结构来自 Templates，协议状态由 `sopify_writer` 管理。

## 目录职责

```text
.sopify/
├── project.md              # 跨任务技术约定
├── user/                   # 长期偏好与原始反馈
├── blueprint/              # 长期目标、设计边界、未完成长期项及索引
├── plan/                   # 当前方案语义文件
├── history/                # 已归档方案与索引
└── state/                  # 本地协议状态
```

`blueprint/README.md` 只保留状态、维护方式、当前目标、当前焦点和阅读入口。深层内容进入对应 blueprint 文件。

## 初始化与渐进物化

`kb_init: full` 首次创建 `project.md`、`user/preferences.md`、`user/feedback.jsonl` 和四个 blueprint 文件；不预建方案正文、history 或空目录。

`kb_init: progressive` 为默认策略：

- 首次真实项目触发：创建 `project.md`、`user/preferences.md`、`blueprint/README.md`。
- 首次进入 plan 生命周期：补齐 `blueprint/background.md`、`blueprint/design.md`、`blueprint/tasks.md` 和当前方案目录。
- 首次显式 `~go finalize`：由协议流程创建 `history/index.md` 和归档目录。
- 首次出现明确长期反馈：按需要创建 `user/feedback.jsonl`。

## 知识上下文读取

宿主先按正式 Protocol 完成 managed plan、handoff 和 receipts 的入口读取。本节只规定 KB 自己的长期知识顺序：

1. `project.md`
2. `user/preferences.md`
3. `blueprint/README.md`
4. 与当前任务有关的 `blueprint/background.md`、`design.md`、`tasks.md`

Consult 和 quick fix 不因缺少深层 blueprint 失败。`history/` 只在追溯或 finalize 时读取。

## 保留与更新

只保留跨任务仍有价值的信息：

- `project.md`：可复用技术约定。
- `background.md`：长期目标、范围和非目标。
- `design.md`：模块、宿主、目录和消费契约。
- `tasks.md`：未完成长期项及有重访条件的明确延后项。
- `preferences.md`：用户明确声明的长期偏好。

不要写入一次性实现细节、当前 plan 的任务拆解、临时取舍、已完成任务或 history 正文副本。代码与文档冲突时先核对代码事实，再修正文档；当前用户指令优先于历史偏好。

## `knowledge_sync`

```yaml
knowledge_sync:
  project: skip|review|required
  background: skip|review|required
  design: skip|review|required
  tasks: skip|review|required
```

- `skip`：本轮不检查该文件。
- `review`：finalize 前确认是否需要更新。
- `required`：交付候选形成前必须更新；未完成时阻断 finalize。

KB 只执行方案声明的同步政策，不改变 plan 生命周期。同步时更新最窄的长期知识位置，避免在多个文件重复同一正文。

## 输出

初始化或同步完成后，先说明实际结果，再列 `Changes`，最后给 `Next:`。没有变化时明确写 `Changes: 0 files`。
