# Copilot Instruction 决策 Spike — 验证记录

> S3 并行决策 spike 产出。为 S4 实现提供依据。

## 1. 运行面支持矩阵

| 运行面 | `copilot-instructions.md` | `*.instructions.md` (路径级) | 备注 |
|--------|:---:|:---:|------|
| VS Code Chat / Edits / Agent | ✅ | ✅ | VS Code ≥ 1.98 |
| GitHub.com Chat (web) | ✅ | ❌ | 路径级文件被静默忽略 |
| Copilot CLI | ✅ | ✅ | 支持 `$HOME/.copilot/` 个人级 |
| Cloud Agent | ✅ | ✅ | 支持 `excludeAgent` |
| Code Review | ✅ (4K cap) | ✅ (4K cap) | 读 base branch，超 4K 静默截断 |

**来源:** https://docs.github.com/en/copilot/reference/custom-instructions-support

### 关键设计事实

- 两种文件**同时加载**，不互相覆盖。冲突时路径级 > 仓库级。
- `applyTo` 可选，不写则不自动匹配（VS Code 可手动附加）。
- `excludeAgent: "code-review"` / `"cloud-agent"` 可排除特定 agent。
- Code Review **硬限 4000 字符**，超出部分静默丢弃。

## 2. 内容来源与边界

**结论：从 bundle 预分发，不从 seed 运行时解析。**

- bundle 目录预存拆分后的两层产物：
  - 轻入口 (< 4K chars)：角色定义 + 核心规则摘要
  - 重说明 (无大小限制)：完整 C1-C4 + A1-A3 规则
- bootstrap 只做复制 + managed block upsert，不做内容解析
- 版本随 `sopify.json.bundle_version` 走，升级时整体替换
- `Copilot/Skills/CN/COPILOT.md` 保留为 source seed / reference（6815 bytes，不被 bootstrap 直接消费）

## 3. frontmatter / applyTo / 源 repo 策略

### frontmatter

```yaml
# .github/instructions/sopify.instructions.md
---
applyTo: "**"
---
```

- `applyTo: "**"` 全匹配：Sopify 规则适用于所有文件
- 当前不需要按路径拆分多个 instructions 文件

### 源 repo (sopify-skills)

- P4d 裁定"不创建 `.github/copilot-instructions.md`"——**继续遵守**
- Bootstrap 产物只在**外部 repo** 生成
- 源 repo 的 Copilot 行为由 AGENTS.md（Codex 侧）和 maintainer 自行管理

### path-specific fallback

- GitHub.com web Chat 不读 `*.instructions.md` → 轻入口必须涵盖核心规则
- 轻入口 < 4K chars，包含：角色定义 + 核心规则摘要 + 指向 sopify.instructions.md 的引用
- 重说明无大小限制

## 4. managed block 策略

### copilot-instructions.md — managed block 模式

```markdown
<!-- BEGIN SOPIFY MANAGED BLOCK v{bundle_version} -->
（Sopify 核心规则摘要）
<!-- END SOPIFY MANAGED BLOCK -->
```

| 操作 | 行为 |
|------|------|
| 首次安装 | append block 到文件末尾（保留用户已有内容） |
| 升级 | regex 替换 BEGIN...END 之间的内容 |
| 用户修改 block 内 | 下次升级覆盖（"managed = 受管理"） |
| 用户修改 block 外 | 不受影响 |
| 卸载 | 删除 managed block，清理空文件 |

参考实现：`bootstrap_workspace.py` L1173-1210（gitignore managed block）

### sopify.instructions.md — owned file 模式

| 操作 | 行为 |
|------|------|
| 首次安装 | 创建文件（frontmatter + 完整内容） |
| 升级 | 整文件替换 |
| 卸载 | 删除文件 |
| 用户修改 | 下次升级覆盖（文件头注释说明"此文件由 Sopify 管理"） |

## 5. S4 实现依据

基于以上验证，S4 实现应：

1. bundle 构建流程从 COPILOT.md seed 预制两层产物
2. bootstrap 在外部 repo 执行 managed block upsert（轻入口）+ owned file 写入（重说明）
3. 轻入口严格 < 4K chars（Code Review 安全）
4. 源 repo 不生成 instruction 文件
5. managed block 复用 gitignore 的 BEGIN/END 标记模式
