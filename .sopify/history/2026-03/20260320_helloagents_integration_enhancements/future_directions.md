# 方法论借鉴：独立 Plan 方向（来自 HelloAGENTS 对比分析）

> 本文件记录从 HelloAGENTS 对比分析中识别出的 4 个方法论借鉴方向。
> 每个方向因范围超出当前 plan（helloagents-integration-enhancements）而需要独立立项。
> 本文件不是 plan，是方向参考；正式立项时应按 Sopify 标准 plan 流程生成 background/design/tasks。

---

## 1. runtime-gate-degradation-mode（渐进式降级）

### 为什么不能进当前 plan

当前 plan 的约束是"不改 runtime 核心契约"（design.md:7），scope 限定在 installer 产品化层。降级模式需要修改 `runtime_gate.py` 的核心判定逻辑——当前 gate 是 all-or-nothing（`gate_passed=true` 才能继续），引入降级意味着要新增 `gate_passed=degraded` 状态，以及配套的 `allowed_response_mode=limited` 处理，这直接触碰 runtime gate contract。

### HelloAGENTS 的做法（参考，不照搬）

HelloAGENTS 的降级哲学是"能力检测 → 最大化利用 → 优雅降级"：
- 6 个 CLI 用同一份 `AGENTS.md` 规则
- 自动检测宿主能力（hooks 是否可用、sub-agent 是否支持、CSV batch 是否可用）
- 缺什么跳过什么，不阻断整个流程
- 关键文件：`helloagents/rules/subagent-protocols.md`（native mechanism mapping + fallback 表）
- 关键模式：`hooks: Optional — features degrade when unavailable`

### Sopify 可以怎么做

不需要做到 6 CLI 降级。核心价值是：当 gate evidence 部分缺失时，允许进入受限模式而不是完全拒绝。

建议方向：
1. `runtime_gate.py` 的 contract 新增 `gate_passed: "degraded"` 状态
2. 定义哪些 evidence 缺失允许降级（例如 `preferences.status != loaded` 可降级，`handoff_found == false` 不可降级）
3. 降级模式下限制可用的 `allowed_response_mode`（例如只允许 `checkpoint_only`）
4. 宿主侧消费 `degraded` 时向用户展示可见警告，而不是静默跳过

### 影响范围

- `scripts/runtime_gate.py` / `.sopify-runtime/scripts/runtime_gate.py`
- `runtime/models.py`（RuntimeGateContract 模型扩展）
- `.sopify-runtime/manifest.json`（`limits.runtime_gate_allowed_response_modes` 扩展）
- CLAUDE.md 宿主接入约定（新增 degraded 处理规则）
- 所有消费 gate contract 的宿主端逻辑

### 前置依赖

无硬依赖，但建议在 helloagents-integration-enhancements（host capability registry）完成后做，因为 registry 的 `support_tier` 可以作为降级决策的输入之一。

---

## 2. develop-verification-loop（开发态质量循环）

### 为什么不能进当前 plan

当前 plan 的 scope 是 installer 层产品化，和 develop skill 的执行逻辑完全无关。质量循环涉及修改 develop skill 的执行规则、增加验证命令发现机制、实现失败重试与根因分析，这是一个独立的 skill 增强。

### HelloAGENTS 的做法（参考，不照搬）

HelloAGENTS 有两个互补的质量循环：

**Ralph Loop（自动验证）：**
- 子智能体完成代码修改后，SubagentStop hook 自动触发项目验证
- 验证命令优先级：`.helloagents/verify.yaml` > `package.json scripts` > auto-detect
- 验证失败 → 子智能体被阻止退出，必须修复（最多 1 次重试）
- 关键文件：`helloagents/hooks/claude_code_hooks.json`（SubagentStop hook 定义）

**Break-Loop（根因分析）：**
- 触发条件：同一任务重复失败
- 五维分析：逻辑错误、类型不匹配、缺失依赖、环境问题、设计缺陷
- 自动在其他模块扫描同类问题
- 经验教训记录到验收报告
- 关键文件：`helloagents/stages/develop.md`（Break-loop 规则）

### Sopify 可以怎么做

不需要实现 hook 系统。核心价值是在 develop skill 的 task 执行循环中加入验证闭环。

建议方向：
1. develop skill 规则中加入"每个 task 完成后执行验证命令"的步骤
2. 验证命令发现机制：`.sopify-skills/project.md` 中的 verify section > `package.json scripts.test` > 无验证可跳过
3. 验证失败时自动重试一次（带上错误上下文），而不是直接标记 task 失败
4. 连续失败 2 次后触发简化版根因分析：检查是逻辑错误还是环境问题，避免无效重试
5. 可选：在 `current_handoff.json` 的 `artifacts` 中记录验证结果，供后续复盘

### 影响范围

- `Claude/Skills/CN/skills/sopify/develop/` 相关规则文件
- `runtime/engine.py`（develop 阶段执行逻辑，如果需要 runtime 支持）
- `.sopify-skills/project.md`（新增 verify section 约定）
- 不影响 runtime gate / handoff / checkpoint 核心契约

### 前置依赖

无硬依赖。可以独立于其他 plan 推进。但如果 models-tests-refactor 先完成，develop skill 的测试拆分会更干净。

---

## 3. lightweight-skill-registration（低门槛 Skill 注册）

### 为什么不能进当前 plan

当前 plan 完全不涉及 skill 体系。Skill 注册涉及 `runtime/builtin_catalog.py`、skill loader、skill.yaml schema 等核心 runtime 组件，远超 installer 产品化范围。

### HelloAGENTS 的做法（参考，不照搬）

HelloAGENTS 的自定义命令机制：
- 用户在 `.helloagents/commands/` 下放一个 `{name}.md` → 自动获得 `~{name}` 命令
- 轻量 gating：只做需求理解 + EHRB 检查
- 不需要 schema 定义、不需要注册入口、不需要 contract_version
- 关键文件：`helloagents/functions/` 目录下 15 个 .md 文件（每个就是一个命令定义）

### Sopify 可以怎么做

不是砍掉结构化 skill 体系，而是在其之上加一层轻量入口。

建议方向：
1. 支持 `.sopify-skills/user/skills/{name}.md` 作为用户自定义 skill
2. 单文件 .md 即是完整 skill：frontmatter 定义 mode/tools/routes，正文是执行规则
3. runtime 自动为单文件 skill 补全缺省 `skill.yaml` 等效配置
4. 用户 skill 的默认权限低于 builtin skill（例如不允许 `allowed_paths: ["/"]`）
5. `runtime/builtin_catalog.py` 扩展为先加载 builtin → 再扫描 user skills → 合并注册

### 影响范围

- `runtime/builtin_catalog.py`（skill 发现与加载逻辑）
- `runtime/engine.py`（skill 执行路径，如果需要区分 builtin/user skill 权限）
- `.sopify-skills/user/skills/` 目录约定
- skill.yaml schema 文档（新增 single-file 格式说明）

### 前置依赖

建议在 models-tests-refactor 完成后推进，因为 `builtin_catalog.py` 的修改会受 models facade 拆分影响。

---

## 4. one-liner-distribution（分发即产品）

### 为什么不能进当前 plan

当前 plan 的 installer 改动限于"让已有安装流程可诊断"，不涉及分发渠道改造。一键安装需要 package registry 发布、安装脚本编写、跨平台适配、交互式菜单等工作，是独立的产品工程。

### HelloAGENTS 的做法（参考，不照搬）

HelloAGENTS 提供 4 种安装方式：
1. **curl | bash**（推荐）：`curl -fsSL .../install.sh | bash` → 自动检测 uv/pip → 验证 Python ≥3.10 → 交互式选目标 CLI → 安装完成
2. **npx**：`npx helloagents`（npm wrapper，底层仍走 pip）
3. **uv**：`uv tool install --from git+... helloagents`
4. **pip**：`pip install git+...`

关键设计决策：
- `cli.py` stdlib-only（无第三方依赖），即使包损坏也能执行基本操作
- `pyproject.toml` 零依赖，最小化安装失败概率
- 安装脚本有自动回退机制（uv 不可用就用 pip）
- 关键文件：`install.sh`（147 行）、`install.ps1`、`pyproject.toml`、`package.json`

### Sopify 可以怎么做

不需要一步到位。分阶段：

**Phase 1 — 基础包发布：**
1. 为 sopify-skills 创建 `pyproject.toml`，定义 `sopify` 命令入口
2. 发布到 PyPI 或支持 `pip install git+...`
3. 保持零依赖或最小依赖

**Phase 2 — 安装脚本：**
1. 编写 `install.sh`（macOS/Linux）和 `install.ps1`（Windows）
2. 自动检测 Python 版本、uv/pip 可用性
3. 交互式菜单选择目标 CLI（codex/claude）
4. 安装后自动执行 `bootstrap_workspace.py`

**Phase 3 — 渠道扩展：**
1. npm wrapper（`npx sopify`）
2. Homebrew formula（macOS）
3. 版本更新检测机制

### 影响范围

- 项目根目录新增：`pyproject.toml`、`install.sh`、`install.ps1`、`package.json`
- `scripts/install_sopify.py`（可能需要重构为可被安装脚本调用的模块）
- `installer/` 目录（可能需要支持从 PyPI 安装后的路径发现）
- CI/CD（发布流水线）
- README.md（安装说明重写）

### 前置依赖

建议在 helloagents-integration-enhancements（host capability registry + doctor）完成后做。registry 提供的 `support_tier` 和 `install_enabled` 可以直接被安装脚本消费，交互式菜单只展示 `install_enabled=true` 的宿主。

---

## 优先级建议

| 方向 | 建议优先级 | 理由 |
|------|-----------|------|
| develop-verification-loop | P2 | 对开发质量有直接提升，无硬依赖，可独立推进 |
| runtime-gate-degradation-mode | P2 | 降低使用门槛，但需要改 runtime 核心契约，影响面需评估 |
| one-liner-distribution | P3 | 对新用户体验提升最大，但工程量大，且依赖 registry 先就绪 |
| lightweight-skill-registration | P3 | 对生态扩展有价值，但当前 builtin skill 覆盖足够，不急 |

建议推进顺序：先完成 models-tests-refactor（当前活跃）→ helloagents-integration-enhancements（本 plan）→ develop-verification-loop → 其余按需选择。
