---
name: cross-review
description: >-
  在开发完成后自动交叉评审代码变更。审查者运行在隔离的 LLM 会话中，
  不继承开发上下文，发现偏差和盲点。Advisory 模式：结论仅供参考，不自动阻断。
---

## 何时触发

在 develop 阶段完成、代码已写入磁盘后触发。不要在规划阶段或未产生代码变更时触发。

前置条件：
- 工作区存在未评审的代码变更（未提交的 `git diff` 非空，或已提交的 review range `git diff <REF>..HEAD` 非空）
- `crossreview` CLI 已安装（`pip install crossreview` 或 `pip install -e .`）
- Reviewer API key 已配置（环境变量 `ANTHROPIC_API_KEY`，或 `crossreview.yaml` 中设置）

## 默认流程（One-Stop）

### Step 0 — 确定 diff 基准并确保变更已提交

CrossReview 的 `--diff REF` 执行的是 `git diff REF HEAD`，只捕获已提交的变更，不包含未暂存或未提交的工作区修改。

**0A — 确定 diff 基准（REF）：**

[IF 任务涉及多次提交]
  REF = HEAD~{提交数}
[ELSE]
  REF = HEAD~1

确认基准：展示 REF 对应的 commit，让用户确认起点正确：
```bash
git log -1 --oneline <REF>
```
[ACTION: INFORM_USER] "Review 起点为：`{REF 对应的 commit 摘要}`。本轮 develop 的所有变更应在此之后。"
若用户认为起点不对，让用户指定正确的 commit SHA 作为 REF。

**0B — 处理未提交变更：**

[IF `git status --short` 非空（工作区存在未提交的 develop 变更）]
  [ACTION: INFORM_USER] 说明 CrossReview v0 只能审查已提交的 diff，当前变更尚未提交。
  [ACTION: ASK_USER] "本轮 develop 产出尚未提交。CrossReview 需要已提交的 diff 才能工作。
  (A) 创建 review commit 并继续评审
  (B) 跳过本次 advisory review"
  - 用户选 A：
    1. 记录当前基准：`BASE_SHA=$(git rev-parse <REF>)`，作为 review range 的稳定起点。
    2. 只 stage 本轮 develop 产生的文件（基于任务清单中的目标文件），不使用 `git add -A`。
    3. 若无法安全区分本轮文件与工作区其他变更，跳过 advisory review 并记录原因 `crossreview_requires_committed_diff`。
    4. 使用任务摘要作为 commit message（如 `"develop: 实现用户认证模块"`），不使用固定泛化消息。
    5. 提交后设置 REF = BASE_SHA。后续 `crossreview verify --diff <REF>` 会稳定审查 BASE_SHA..HEAD，包含本轮所有已提交变更和刚创建的 review commit。
  - 用户选 B：
    跳过 advisory review，记录原因 `user_skipped_uncommitted`，继续主流程。

[ELSE IF `git status --short` 为空（工作区干净）]
  检查已提交的 review range：`git diff <REF>..HEAD`。
  [IF review range 非空]
    变更已在 HEAD 中，继续 Step 1。
  [ELSE]
    无代码变更，跳过评审。

重要：不要自动 `git add -A && git commit`。这会把工作区所有变更（包括无关草稿、未跟踪文件）一起提交，违反安全边界。

### Step 1 — 执行评审

```bash
crossreview verify --diff <REF> --format human
```

可选参数（按需添加）：
- `--intent "任务意图摘要"` — 帮助审查者理解变更目标
- `--task ./task.md` — 任务描述文件
- `--context ./plan.md` — 额外上下文文件（可重复）
- `--focus <area>` — 聚焦区域（可重复）

完整示例：
```bash
crossreview verify --diff HEAD~1 \
  --intent "修复用户认证逻辑" \
  --task ./task.md \
  --context ./plan.md \
  --format human
```

### Step 2 — 读取输出

命令成功时（exit code 0），输出格式为：

```
CrossReview 0.1-alpha | artifact: <hash> | review_status: <status>

Intent: <intent>
Intent Coverage: covered/partial/unknown
Pack Completeness: 0.XX

Findings (N):
  [HIGH]  file.py:42 — 发现摘要
  [MED]   other.py — 另一个发现

Advisory Verdict: <verdict>
  Rationale: <理由>
```

关键字段：
- `review_status` — `complete` / `rejected` / `failed`
- `Advisory Verdict` — 见 Step 3 分支

### Step 3 — 根据 verdict 分支处理

[IF review_status != "complete"]
  [ACTION: LOG_WARNING] 记录非正常状态（rejected / failed），继续主流程，不阻断。
  [SKIP] 不进入以下 verdict 分支。

[IF Advisory Verdict == "pass_candidate"]
  [ACTION: CONTINUE]
  告知用户：评审未发现问题，代码可以继续推进。

[IF Advisory Verdict == "concerns"]
  [ACTION: SHOW_FINDINGS] 向用户展示所有 findings（按严重度排列）。
  [ACTION: ASK_USER] "评审发现以下问题：\n{findings}\n(A) 修改代码后重新评审 (B) 接受并继续 (C) 忽略"
  - 用户选 A → 修改代码，回到 Step 0 重新执行
  - 用户选 B 或 C → 继续主流程

[IF Advisory Verdict == "needs_human_triage"]
  [ACTION: SHOW_FINDINGS] 展示所有 findings。
  [ACTION: REQUEST_HUMAN] "评审发现需要人工判断的复杂问题，请审阅后决定。"
  等待用户明确指令后再继续。

[IF Advisory Verdict == "inconclusive"]
  [ACTION: LOG_WARNING] "评审结果不确定，可能由于上下文不足或模型限制。"
  继续主流程，不阻断。

## 备用流程（Pack 模式）

仅在 `verify --diff` 失败时使用（如 git 不可用、diff 过大）：

```bash
crossreview pack --diff <REF> --intent "任务摘要" > pack.json
crossreview verify --pack pack.json --format human
```

verdict 处理同 Step 3。

## 重要约束

- **Exit code 0 = 结果已产出**，不代表评审通过。必须读 `Advisory Verdict` 行判断。
- **Exit code 非零 = 命令执行失败**，无评审结果。记录错误，继续主流程。
- **Advisory 模式：verdict 仅供参考，不自动阻断任何流程。**
- 不要在无代码变更时运行（浪费 token）。
- `--format human` 用于终端展示，`--format json` 用于程序解析。

## 交付检查

- [ ] crossreview 命令成功执行（exit code 0）
- [ ] Advisory Verdict 已读取并展示给用户
- [ ] concerns / needs_human_triage 时用户已被告知并做出决定
- [ ] 结果不阻断主流程（advisory only）
