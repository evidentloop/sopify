---
name: templates
description: 知识库文档模板；创建或补齐长期知识文件时按需读取。
---

# 知识库模板

Templates 只定义稳定的知识库文档结构，不决定写入时机、同步政策或方案生命周期。

- 知识库规则与 `knowledge_sync`：读取 `kb` Skill。
- 方案级别 `light / standard / architecture` 及方案正文模板：读取 Design `assets/`。
- 活动方案、handoff 和 receipts 的读取与写入：遵循正式 Protocol。

使用模板时替换占位符，删掉无内容的可选区块。不要把一次性实现细节写进长期知识。

## `project.md`

```markdown
# 项目技术约定

## 技术栈
- 核心: {语言或框架版本}
- 构建: {构建工具}
- 测试: {测试框架}

## 使用约定
- {跨任务可复用的技术约定}

## 文档边界
- `project.md`: 技术约定
- `blueprint/background.md`: 长期目标、范围与非目标
- `blueprint/design.md`: 模块、宿主、目录与消费契约
- `blueprint/tasks.md`: 未完成长期项与明确延后项
```

## `blueprint/README.md`

```markdown
# 项目蓝图索引

状态: {当前状态}
维护方式: 只保留状态、当前目标、当前焦点和阅读入口

## 当前目标
- {长期目标摘要}

## 当前焦点
- 活动方案: {无 / 链接到 plan.md}
- 归档状态: {状态}

## 深入阅读
- [项目技术约定](../project.md)
- [背景](./background.md)
- [设计](./design.md)
- [任务](./tasks.md)
- [变更历史](../history/index.md)
```

如 `blueprint/` 根目录有长期专题文档，在“深入阅读”中逐项列出。

## `blueprint/background.md`

```markdown
# 蓝图背景

## 长期目标
- {目标}

## 范围
- 范围内: {内容}
- 范围外: {内容}

## 非目标
- {内容}
```

## `blueprint/design.md`

```markdown
# 蓝图设计

## 正式契约
- {跨方案持续有效的契约}

## 模块与消费边界
- {模块、宿主或目录职责}
```

## `blueprint/tasks.md`

```markdown
# 蓝图任务

## 未完成长期项
- [ ] {长期项}

## 明确延后项
- [-] {延后项与重访条件}
```

只保留未完成长期项和明确延后项，不保留 `[x]` 项。

## `history/index.md`

```markdown
# 变更历史索引

| 日期 | 功能 | 状态 | 方案包 |
|------|------|------|--------|
| {YYYY-MM-DD} | {功能} | {状态} | [链接](YYYY-MM/...) |
```

## `user/preferences.md`

```markdown
# 用户长期偏好

- {用户明确声明、可跨任务复用的偏好}
```

## `user/feedback.jsonl`

```json
{"timestamp":"{ISO-8601}","source":"chat","message":"{原始反馈}","scope":"{范围}","promote_to_preference":false}
```
