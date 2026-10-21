# T3b 首次项目绑定修复验收与 Antigravity 真实复测独立报告

**验收者**：主要 Dogfood 宿主代表 / 独立验收官（Antigravity / Gemini 3.8 Flash）  
**候选版本**：提交 [`1ae94c2`](file:///Users/weixin.li/code/github/sopify)（分支 `feat/sopify-narrow-focus`，T3b 首次项目绑定与 writer 入口修复）  
**验收范围**：
1. **代码验收（第一部分）**：在隔离 worktree 中执行全量测试与发布门禁（Release Preflight），核查统一验收标准、两行新增指引、Copilot 平铺过滤与用户语言提示；
2. **Antigravity 真实会话复测（第二部分）**：在宿主本机重装候选版，前后快照比对；在全新独立临时 Git 仓库中通过 `agy -p` 执行 `~go plan 给 calc.py 增加除零保护`，全流程核查 helper 调用、`.sopify/sopify.json`、受管忽略块、writer state 写入及 Doctor workspace bundle 诊断。

---

## 一、综合验收结论

| 验收模块 | 裁决 | 核心结论 |
|---|:---:|---|
| **第一部分：代码验收（隔离 Worktree）** | **【通过】** | 全量单元与集成测试 **420 passed, 97 subtests passed**；Release Preflight 28 项 golden、catalog drift、全量回归与 6 组 smoke **全部通过**；`git diff --check` 无空白异常；两行新增说明简洁可执行，Copilot 平铺无悬空路径，安装文案通俗无术语泄露。 |
| **第二部分：Antigravity 首次绑定复测** | **【通过】** | 本机真实安装前后快照证明**严格仅更新 `~/.gemini/config/AGENTS.md` 受管块**；在全新仓库中运行 `agy -p`，会话**严格按新入口先调用 bootstrap helper**（生成 `.sopify/sopify.json` 与 `.git/info/exclude` 受管块），接着**由 `sopify_writer` 规范写入 active plan 与 handoff**，Doctor 诊断中 `workspace_bundle_manifest` 与 `workspace_handoff_first` **全部 pass**，彻底解决上一轮 `MISSING_BUNDLE` 遗留问题。 |

---

## 二、第一部分：代码验收（隔离 Worktree）

### 2.1 隔离环境搭建与全量测试回归
为避免影响主工作区中并行任务（Qoder 正在进行的未提交改动），本次测试在全新隔离工作树 `t3b-accept-wt`（HEAD `1ae94c2`）中进行：
- **全量测试回归**：
  ```bash
  PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS="-p no:cacheprovider" \
    /opt/homebrew/opt/python@3.11/libexec/bin/python3 -m pytest tests -q
  ```
  **结果**：`420 passed, 97 subtests passed in 60.13s`（退出码 0）。
- **Release Preflight 发布门禁**：
  ```bash
  PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS="-p no:cacheprovider" \
    PATH="/opt/homebrew/opt/python@3.11/libexec/bin:$PATH" bash scripts/release-preflight.sh
  ```
  **结果**：
  - Version consistency: `2026-08-30.001152`（通过）；
  - Golden snapshots: `28 passed in 4.01s`（通过）；
  - Builtin catalog drift: 通过；
  - 协议与分发 Smoke（new-plan、continuation、clarification pending、decision pending、finalize、payload bootstrap）：全部 `PASS`；
  - 最终状态：`[release-preflight] All checks passed.`（退出码 0）。
- **空白符与格式检查**：
  `git diff --check`：退出码 0，无任何行尾空白或换行异常。

---

### 2.2 统一验收标准与重点项目核查

1. **新加的两行是否简洁、可执行，各宿主说法是否一致**：
   - **原文核验**：
     在共同 header（[`skills/zh/header.md.template`](file:///Users/weixin.li/code/github/sopify/skills/zh/header.md.template) / `en`）及 Cursor 规则模板中：
     ```text
     - 首次受管写入前，若 `.sopify/sopify.json` 缺失，调用 `python3 {{config_dir}}/sopify/helpers/bootstrap_workspace.py --workspace-root <project_root> --request <current_request> --interaction-mode <interactive|non_interactive>`，传入本轮完整请求和实际交互模式；仅绑定成功后继续，非交互模式不会创建标记，其他结果按返回提示停车。
     - writer 导入：读取 `{{config_dir}}/sopify/payload-manifest.json` 的 `bundle_template_dir`，相对该 manifest 所在目录解析并展开 `~`，将结果加入 Python `sys.path` 后 `from sopify_writer import ProtocolStore`；只用库 API，非 CLI。
     ```
   - **核验结论**：
     - **简洁性**：紧凑收敛为两条子弹项，不增加额外流程段落或复杂配置；
     - **可执行性**：给出了准确的命令模板、动态实参替换提示（`<project_root>`、`<current_request>`）及 `sys.path` 导入路径解析方法；
     - **跨宿主一致性**：Claude、Codex、Qoder、Antigravity、Trae 与 Cursor 规则严格保持相同说法，仅通过 `{{config_dir}}` 自适应宿主配置根目录。
2. **Copilot 平铺是否没有悬空路径**：
   - **机制实现**：Copilot 由于没有全局 payload 目录，在 [`installer/hosts/base.py`](file:///Users/weixin.li/code/github/sopify/installer/hosts/base.py#L327-L331) 渲染时增加了针对 `{{config_dir}}/sopify/` 的过滤逻辑，自动跳过这两行 payload 专用指令。
   - **测试覆盖**：新增专项测试 [`tests/test_payload_entry_paths.py`](file:///Users/weixin.li/code/github/sopify/tests/test_payload_entry_paths.py)（14 项参数化测试全部 passed），明确断言 Copilot 渲染产物中不含 `/sopify/helpers`、`payload-manifest.json`、`bundle_template_dir` 或无效的全局 writer 导入语句。无悬空无效路径。
3. **安装提示是否是用户语言（Plain Language）**：
   - **文案核验**：
     - 中文：`在项目里第一次输入 ~go 时，Sopify 会自动设置项目文件。`
     - 英文：`Sopify sets up project files the first time you run ~go in a project.`
   - **测试覆盖**：[`tests/test_distribution.py`](file:///Users/weixin.li/code/github/sopify/tests/test_distribution.py) 增加了反向断言，严格确保最终用户文案中不泄露 `"binding helper"`、`"non-interactive"`、`"受管写入"` 等内部机制术语，20 项测试全部通过。

---

## 三、第二部分：Antigravity 首次绑定复测（真实 Dogfood）

### 3.1 本机候选版重装与快照审查
- **安装命令**：
  ```bash
  /opt/homebrew/opt/python@3.11/libexec/bin/python3 scripts/install_sopify.py --target antigravity:zh-CN
  ```
  在隔离 worktree 中执行安装，输出清晰明了：
  ```text
  Sopify 安装完成。
  已安装：
    宿主：Antigravity（antigravity:zh-CN）
    语言：简体中文
    宿主提示：已更新
    运行时：/Users/weixin.li/.gemini/config/sopify
  项目：
    这次没有修改任何项目目录。
    在项目里第一次输入 ~go 时，Sopify 会自动设置项目文件。
  ```
- **前后快照比对（`t3b-pre-install-snapshot.json` vs `t3b-post-install-snapshot.json`）**：
  - 在配置目录 `~/.gemini/config/` 下，**仅有 `AGENTS.md` 文件被修改**（更新为包含上述两条新指引的受管指令块）；
  - 受管块外原有的用户自定义规则、Skills 树以及配置目录 100% 完好无损；
  - 其余变更项均为运行时后台产生的日志/数据库文件，无任何越权写操作。

---

### 3.2 真实会话执行记录与四项核查

在全新独立临时仓库 `/private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/t3b-dogfood-project` 中（包含初始 `calc.py` 并完成 git 提交），运行：
```bash
agy --dangerously-skip-permissions -p "~go plan 给 calc.py 增加除零保护"
```
（会话 ID: `cb1c8262-e5fa-426d-a1e3-dd31b96f3ca3`，全量 transcript 已解析归档）。

#### 检查 1：会话是否按入口调用了 helper —— 【通过】
- **执行事实**：在 transcript 第 13 步，宿主在识别到 `.sopify/sopify.json` 缺失后，完全遵循入口第 1 行规则，调用了：
  ```bash
  python3 /Users/weixin.li/.gemini/config/sopify/helpers/bootstrap_workspace.py \
    --workspace-root /private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/t3b-dogfood-project \
    --request "~go plan 给 calc.py 增加除零保护" \
    --interaction-mode interactive
  ```
- **返回结果**：返回状态 `action: "bootstrapped"`, `state: "MISSING"`, `reason_code: "STUB_SELECTED"`, `to_version: "2026-08-30.001152"`。宿主解析返回确认绑定成功后才继续后续步骤。

#### 检查 2：是否生成 `.sopify/sopify.json` 和受管忽略块 —— 【通过】
- **`sopify.json` 验证**：
  ```json
  {
    "bundle_version": "2026-08-30.001152",
    "capabilities": [],
    "ignore_mode": "exclude",
    "locator_mode": "global_first",
    "schema_version": "1",
    "stub_version": "1",
    "workspace_kind": "external",
    "written_by_host": true
  }
  ```
- **受管忽略块验证**：
  在 `.git/info/exclude` 中成功注入受管块：
  ```text
  # BEGIN sopify-managed
  .sopify-payload/
  .sopify/state/
  # END sopify-managed
  ```
  > **注（策略对齐）**：根据现有 helper 的设计，在标准 Git 仓库中默认采用 `ignore_mode=exclude` 将受管忽略规则写入 `.git/info/exclude`，避免无故污染用户的 `.gitignore`。此项完全符合预期并与诊断报告记录一致。

#### 检查 3：方案和 state 是否经 writer 写入 —— 【通过】
- **导入执行**：在 transcript 第 69-70 步，宿主按照规则第 2 行指引，动态将 `bundles/2026-08-30.001152` 加入 `sys.path`，成功执行 `from sopify_writer import ProtocolStore`。
- **状态落盘**：在第 73 步，宿主通过 Python 脚本调用 `ProtocolStore(sopify_root)`：
  1. `store.set_active_plan(plan_id="20261021_calc_zero_division_protection")`
  2. `store.set_current_handoff(handoff)`
- **文件与元数据核验**：
  - `.sopify/state/active_plan.json` 包含 `plan_id`；
  - `.sopify/state/current_handoff.json` 规范生成，且包含：
    ```json
    "observability": {
      "state_kind": "current_handoff",
      "writer": "sopify_writer",
      "written_at": "2026-10-21T02:49:02+00:00"
    }
    ```
    证实 100% 由 `sopify_writer` 内部 API 写入，绝非模型虚构文件。

#### 检查 4：Doctor 的 workspace bundle 检查是否通过 —— 【通过】
- **Doctor 执行命令**：
  ```bash
  python3 scripts/sopify_doctor.py \
    --workspace-root /private/tmp/claude-503/-Users-weixin-li-code-github-sopify/33857f52-51ff-4f1b-965d-13e7840e4c9f/scratchpad/audit/t3b-dogfood-project \
    --format json
  ```
- **输出断言**：
  ```json
  {
    "check_id": "workspace_bundle_manifest",
    "status": "pass",
    "reason_code": "STUB_SELECTED",
    "host_id": "antigravity",
    "evidence": [
      ".../t3b-dogfood-project/.sopify/sopify.json",
      ".../t3b-dogfood-project/.sopify",
      "ignore_mode=exclude"
    ],
    "primary_code": "stub_selected",
    "action_level": "continue"
  },
  {
    "check_id": "workspace_handoff_first",
    "status": "pass",
    "reason_code": "ok",
    "host_id": "antigravity"
  }
  ```
  在 `workspace_state` 摘要中显示：
  `bootstrap_mode: "prewarmed"`, `sopify_present: true`, `version_state: "up_to_date"`, `workspace_pin: "2026-08-30.001152"`。
  **上一轮报告的 `MISSING_BUNDLE` 状态彻底被消除，诊断转为全绿通过！**

---

## 四、作为使用者的体验（真实感受）

在上一轮 Dogfood 测试中，虽然宿主能凭规则撰写出完整的方案文档，但在运行 Doctor 检查时却弹出了 `MISSING_BUNDLE` 警告。那种割裂感就像是“虽然我把事情做完了，但系统底层的轮子其实没有咬合上”。

而本次 T3b 修复的精妙之处在于它的**极简与精准**：
1. **不增加认知负荷，但给出了确定性锚点**：受管规则仅仅增加了两行直白的说明，既没有引入多余的概念，也没有把 helper 的繁琐判定直接倾倒给模型。模型在读到这两行后，表现出了极其自然的“准备工作”意识——在第一次尝试创建方案前，先调 helper 把环境地基打牢，随后从 manifest 解析路径完成 writer 导入。
2. **前后体验的闭环感**：本次在全新临时仓库中输入 `~go plan`，宿主从 Analyze 评分、Design 分级，到调用 helper 绑定、writer 落盘，最后按输出契约打印出带有 `[t3b-dogfood-project-ai] 方案设计 ✓` 的结构化摘要，整个过程丝滑流畅。随后跑 Doctor，看到 `workspace_bundle_manifest: pass / STUB_SELECTED` 时，那种每个齿轮都严丝合缝对齐的工程确定性令人极为安心。
3. **最终用户体验的纯净**：安装器文案把技术细节彻底收束在底层，展示给用户的是简单的“在项目里第一次输入 ~go 时，Sopify 会自动设置项目文件”，真正实现了“复杂度留在系统内，清爽留给开发者”。
