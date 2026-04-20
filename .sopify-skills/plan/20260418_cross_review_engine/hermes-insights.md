# 参考洞察：Hermes Agent 架构对 CrossReview 的设计启发

> **文档状态：持续演进**
> 本文档基于对 `hermes-agent`（NousResearch）源码的代码级分析，目标是提取对 CrossReview 设计有直接参考价值的机制。
> 不是架构抄袭，而是：相同问题，不同形态，取长补短。
>
> **如何使用本文档**：
> - 当 `design.md` 中某个设计决策遇到选择分叉时，先来这里查是否有 Hermes 的类比机制
> - 当发现 design.md 有新的 "Hermes 可以补充" 的空白时，先写到本文档的"待补充"区块，再合并进 design.md

---

## 一、最关键洞察：CrossReview 的核心理念已经在 Hermes 里以 Skill 形式存在

`hermes-agent/skills/software-development/requesting-code-review/SKILL.md` 第一行：

> **"No agent should verify its own work. Fresh context finds what you miss."**

这就是 CrossReview 的 `verification loop` 概念。差异在于：

| 维度 | Hermes（Skill 形式） | CrossReview（目标形式） |
|---|---|---|
| 触发方式 | LLM 读 Markdown 后自主决定 | policy 配置 + runtime 确定性触发 |
| artifact 输入 | 自然语言描述 diff | 结构化 review_pack（code_diff / plan_package） |
| reviewer | subagent via `delegate_tool`（LLM 主导） | fresh_session / cross_model reviewer（runtime 编排） |
| 输出 | 自然语言点评 | finding / verdict / adjudication（结构化 contract） |
| 沉淀 | 无（只在当前 turn 产生） | `review.md` → plan asset → history（可审计） |
| 可配置性 | 无（Markdown 写死） | policy（advisory/required/block 三档） |

**设计启示**：CrossReview 不是在发明新概念，而是把 Hermes 验证直觉**工程化**：
- 从"LLM 读 Markdown 决定要不要验证" → "runtime 按 policy 确定性触发"
- 从"自然语言点评" → "结构化 finding/verdict contract"
- 从"当次消失" → "进入 plan 生命周期，可审计"

---

## 二、Hermes 架构与 Sopify/CrossReview 的根本差异

### 2.1 Agent Loop 范式

| | Hermes | Sopify / CrossReview |
|---|---|---|
| 工作单元 | `session + conversation turn` | `plan lifecycle + route` |
| 主循环 | `AIAgent.run_conversation()` — while 循环，最多 90 次 iteration | `run_runtime()` — 确定性路由，单 route，无内部循环 |
| 状态载体 | SQLite `state.db`（FTS5 全文检索） | 文件 `current_handoff.json`（结构化 contract） |
| 谁决定做什么 | **LLM 自己决定**（via tool calls） | **runtime router 决定**（确定性分类） |

**代码证据**：
- `hermes/run_agent.py:8802` — `run_conversation()` while 循环
- `sopify/runtime/engine.py:603` — `run_runtime()` if/elif route dispatch chain

### 2.2 工具 vs 技能范式

| | Hermes | Sopify |
|---|---|---|
| 工具形式 | OpenAI function call（LLM 主动调用） | Python runtime skill（router 决定调用） |
| 技能形式 | Markdown prompt 注入 system prompt | Python 模块，`run_{skill_id}_runtime` 入口约定 |
| 并发 | 最多 8 个工具并发执行（ThreadPoolExecutor） | 串行，一次 route 一个 skill |

### 2.3 检查点范式

| | Hermes | Sopify |
|---|---|---|
| 检查点类型 | 文件系统快照（shadow git repo，对 LLM 透明） | 语义决策点（clarification/decision/execution_confirm） |
| 触发方式 | write_file/patch 前自动触发 | 需要用户拍板时主动 checkpoint |
| 实现 | `tools/checkpoint_manager.py` — shadow git repo | `develop_checkpoint.py` + `handoff.py`：`required_host_action` |
| 恢复方式 | git rollback | 重新调用 runtime，从 current_run.json 继续 |

**启示**：Hermes 的检查点是"工件快照"（做错了可以回退）；Sopify 的检查点是"决策节点"（需要人确认才能继续）。CrossReview 的 `review.md` 和 `finding/verdict` 更接近 Sopify 的语义，不需要引入 Hermes 的快照机制。

---

## 三、Hermes Skill 学习机制详解

### 3.1 三层机制

**层 1：Skills = Markdown 程序性记忆**

```
~/.hermes/skills/
└── software-development/
    ├── requesting-code-review/
    │   └── SKILL.md     # 含 front matter + step-by-step 过程
    ├── subagent-driven-development/
    │   └── SKILL.md
    └── ...
```

Front matter 结构（`SKILL.md` 示例）：
```yaml
---
name: requesting-code-review
version: 2.0.0
tags: [code-review, security, verification, quality, pre-commit]
related_skills: [subagent-driven-development, writing-plans]
---
```

**层 2：Agent 自主创建/更新 Skill**（`tools/skill_manager_tool.py`）

```python
# LLM 完成复杂任务后，主动调用：
skill_manager_tool.create(name="pattern-x", content="...")
skill_manager_tool.edit(name="pattern-x", content="...")
skill_manager_tool.patch(name="pattern-x", old="...", new="...")
```

关键：不需要用户触发，agent 自己判断"这个经验值得沉淀"。`skills` 是"程序性记忆"（how to do）。

**层 3：安全扫描**（`tools/skills_guard.py`）

Agent 写入的新 skill 过 `scan_skill()` 防注入检查：
```python
_CONTEXT_THREAT_PATTERNS = [
    (r'ignore\s+(previous|all|above|prior)\s+instructions', "prompt_injection"),
    (r'system\s+prompt\s+override', "sys_prompt_override"),
    ...
]
```
和社区 Hub 安装的 skill 同等待遇。

### 3.2 Hermes 知识分层

```
全局知识（用户级）：
  ~/.hermes/skills/        # 跨项目，程序性知识（如何做某件事）
  ~/.hermes/state.db       # 跨项目，历史对话 FTS5 检索
  ~/.hermes/MEMORY.md      # 跨项目，陈述性记忆（关于用户/偏好）

项目知识（目前没有）：
  Hermes 不区分项目内 vs 全局，所有 skills 都是全局的
```

对比 Sopify：
```
全局知识：
  ~/.claude/sopify/        # 只有安装物和 helpers，没有知识
  ~/.sopify/skills/        # 暂无，但需要（见 §4.2 借鉴建议）

项目知识：
  .sopify-skills/blueprint/ # 项目内结构化上下文（陈述性）
  .sopify-skills/history/   # 已完成方案归档
```

**缺口**：Sopify 缺少"全局可复用 AI 操作程序"层。

---

## 四、对 CrossReview 设计的具体借鉴建议

### 4.1 借鉴 1：blueprint 自动更新（类 skill auto-capture）

**Hermes 机制**：任务完成后，agent 自主调用 `skill_manager_tool.create()` 把经验转成可复用 skill。

**CrossReview 可借鉴的方向**：

在 `review.md` 的 `final_verdict` 确认后，CrossReview 触发一步**经验抽取**：
- 把本次 plan 的高置信度、高频 finding（如"该项目 auth 模块历史上有 expiry bypass 风险"）提炼到 `blueprint/patterns.md`
- 粒度是**项目级可复用风险模式**，不是全局过程

效果：下次同项目启动 design review 时，adjudicator 可以加载 `blueprint/patterns.md` 里的历史模式作为额外权重。

**当前方案包中的挂接点**：
- 触发时机：finalize 时 `final_verdict == "pass"` 后
- 产出文件：`blueprint/patterns.md`（当前方案包中未规划，建议 Phase 2 补充）
- 任务映射：当前 `3.3 明确 finalize 集成切入点` 中可以加这一步

### 4.2 借鉴 2：全局 CrossReview 知识层

**Hermes 机制**：`~/.hermes/skills/` 全局共享，跨项目复用。

**CrossReview 可借鉴的方向**：

建立 `~/.crossreview/rubrics/` 目录，存放跨项目通用的 review rubric：
```
~/.crossreview/rubrics/
└── code-review/
    ├── auth-patterns.md     # 通用 auth 安全检查列表
    ├── api-contracts.md     # API 变更风险检查
    └── migration-risks.md   # DB migration 审查清单
```

这些 rubric 在 reviewer 编排时自动注入，作为结构化背景知识，类似 Hermes skill 注入 system prompt 的方式。

**与项目级 blueprint 的分工**：
- `~/.crossreview/rubrics/`：**如何 review**（通用过程，跨项目）
- `.sopify-skills/blueprint/patterns.md`：**这个项目的已知风险**（项目内知识）

### 4.3 借鉴 3：review 输出的知识沉淀管道

**Hermes 机制**：Skill 有 `version` 字段，`edit/patch` 机制让 skill 持续演进。

**CrossReview 可借鉴的方向**：

`review.md` 的 `finding` 经过多次 plan 积累后，可以形成项目的"review 知识库"：
- 已修复的历史 finding → `blueprint/patterns.md` 的"已知问题/已解决"清单
- 重复出现的 finding → 触发策略升级（advisory → required）
- 高置信度 finding → 沉淀为 deterministic checker 规则

这个管道 Hermes 没有对等物（Hermes skill 是全局的，没有项目级积累机制）。CrossReview 可以在这里做出比 Hermes 更深的东西。

### 4.4 借鉴 4：skill 安全扫描模式

**Hermes 机制**：`skills_guard.py` 对 LLM 写入的 skill 扫描 prompt injection。

**CrossReview 的对应场景**：

当 CrossReview 把 finding 自动写入 `review.md` 和 `blueprint/patterns.md` 时，相同风险存在（恶意代码中的注释可能被 reviewer 误识别为指令并写入文档）。

建议在 `review_pack` 的 artifact 处理层加类似的扫描：
- 扫描 `code_diff` 中注释里的 meta-instruction 模式
- 扫描 `plan_package` 中可能的注入尝试
- 对写入 `review.md` 的 finding.title/summary 字段做 sanitize

---

## 五、两种知识沉淀策略的对比（核心洞察）

| | Hermes | Sopify（当前） | CrossReview（目标） |
|---|---|---|---|
| 知识类型 | 程序性（**如何做**某件事） | 陈述性（**这个项目是**什么状态）| **两者都需要** |
| 写入时机 | agent 自主判断 | 生命周期事件触发 | 生命周期事件触发（保持 Sopify 风格） |
| 知识粒度 | 全局可复用过程 | 项目内结构化上下文 | 项目级风险模式 + 全局 review rubric |
| 检索方式 | system prompt 注入 + FTS5 | 文件系统读取 | 文件系统读取（保持 Sopify 风格） |

**CrossReview 是第一个需要两种知识沉淀都做的 Sopify 能力**：
- 项目级：这个项目历史上的高频风险 → `blueprint/patterns.md`
- 全局级：通用 review rubric → `~/.crossreview/rubrics/`

---

## 六、待补充区块

> 以下是后续深入分析时应继续完善的方向：

- [x] SkillGuidedReviewer 设计（已完成，见 §8）
- [ ] Hermes `subagent-driven-development` skill 的"两阶段 review"与 CrossReview design/develop 分阶段集成的对应分析
- [ ] Hermes `mixture_of_agents_tool.py` 的并发 fan-out 与 CrossReview reviewer orchestration 的设计对比
- [ ] Hermes `context_compressor.py` 的 session 压缩机制 vs CrossReview review_pack 的 artifact 截断策略
- [ ] Hermes FTS5 跨 session 检索 vs CrossReview `blueprint/patterns.md` 项目级历史的检索机制设计

---

## 七、本文档与 design.md 的关系

当本文档中某个借鉴建议被**正式拍板**后，应：

1. 在 `tasks.md` 中新增对应任务（如 `Phase 2: 补充 blueprint/patterns.md 写入机制`）
2. 在 `design.md` 的对应章节补充设计细节（如"与 Sopify 的集成边界 > finalize 集成"）
3. 本文档对应条目标记 `→ 已合并进 design.md`，并留链接

未被拍板的内容继续在本文档演进，不提前污染主设计文档。

---

## 八、SkillGuidedReviewer：CrossReview 复用 Hermes Skill 的接口设计

> **状态：已拍板方向，待写入 design.md**

### 8.1 核心发现：Hermes skill Steps 1-4 = CrossReview review_pack 构建

`requesting-code-review/SKILL.md` 步骤分解：

| Hermes 步骤 | 做的事 | CrossReview 对应 |
|---|---|---|
| Step 1 | `git diff --cached` | `review_pack.artifact.diff` |
| Step 2 | 静态安全扫描（grep 模式）| `deterministic_checker` reviewer |
| Step 3 | 跑测试，记 baseline failures | `review_pack.evidence.tests` |
| Step 4 | Quick code scan | `review_pack.evidence.snippets` |
| **Step 5** | **独立 reviewer subagent（`delegate_task`）** | **`fresh_session_same_model` reviewer** |

Steps 1-4 = CrossReview 的 review_pack 构建阶段；Step 5 = reviewer 执行阶段。两者不重叠，可以组合。

`delegate_tool.py` 的关键约束和 CrossReview reviewer 要求完全吻合：
- 隔离上下文（fresh session，no parent history）
- 只看 artifact + evidence（no producer context）
- 不能递归 delegate（`MAX_DEPTH = 2`）

### 8.2 Reviewer Transport Protocol

```python
class ReviewerTransport(Protocol):
    reviewer_id: str
    reviewer_type: str

    def execute(self, review_pack: ReviewPack) -> RawReviewerOutput: ...

class RawReviewerOutput:
    reviewer_id: str
    content: str               # 原始输出（自然语言或 JSON 字符串）
    output_format: str         # "structured_json" | "free_form" | "deterministic"
    metadata: dict
```

**三种实现**：

| 类型 | 描述 | 输出格式 |
|---|---|---|
| `NativeStructuredReviewer` | CrossReview 内置，直接 JSON finding | `structured_json` |
| `SkillGuidedReviewer` | 外部 Markdown skill（含 Hermes skill）作为过程指导 | `free_form` |
| `DeterministicChecker` | lint/test/schema rule，无 LLM | `deterministic` |

### 8.3 SkillGuidedReviewer 实现

```python
class SkillGuidedReviewer(ReviewerTransport):
    reviewer_type = "skill_guided"

    def __init__(self, skill_path: str, model: str = None):
        self.skill_path = Path(skill_path).expanduser()
        self.model = model

    def execute(self, review_pack: ReviewPack) -> RawReviewerOutput:
        skill_procedure = self._load_skill_procedure()
        prompt = self._build_reviewer_prompt(review_pack, skill_procedure)
        raw_output = call_llm_isolated_session(
            prompt=prompt,
            model=self.model,
            system="You are an independent code reviewer. Review only what is in the provided context."
        )
        return RawReviewerOutput(
            reviewer_id=self.reviewer_id,
            content=raw_output,
            output_format="free_form"
        )

    def _load_skill_procedure(self) -> str:
        """提取 SKILL.md 的程序性内容：跳过 front matter 和 When to Use，保留 Step N: 章节。"""
        skill_md = (self.skill_path / "SKILL.md").read_text()
        return extract_instructional_content(skill_md)

    def _build_reviewer_prompt(self, review_pack: ReviewPack, skill_procedure: str) -> str:
        return f"""REVIEW PROCEDURE:
{skill_procedure}

INPUT TO REVIEW:
Task: {review_pack.task.request}
Acceptance criteria: {review_pack.task.acceptance_criteria}

Code diff:
{review_pack.artifact.diff}

Evidence:
- Tests: {review_pack.evidence.tests}
- Snippets: {review_pack.evidence.snippets}

Risk context: {review_pack.policy_context.risk_tags}

Follow the review procedure above. Focus on what's in the diff and evidence."""
```

**配置示例**：

```yaml
cross_review:
  reviewers:
    - id: hermes_code_review
      type: skill_guided
      skill_path: ~/.hermes/skills/software-development/requesting-code-review/
      enabled: true

    - id: native_structured
      type: fresh_session_same_model
      enabled: true

    - id: lint_check
      type: deterministic_checker
      command: "ruff check {files}"
      enabled: true
```

### 8.4 FindingNormalizer：统一归一化层

```python
class FindingNormalizer:
    def normalize(self, raw: RawReviewerOutput, artifact_kind: str) -> list[Finding]:
        if raw.output_format == "structured_json":
            return parse_json_findings(raw.content)          # NativeStructured 输出
        elif raw.output_format == "deterministic":
            return parse_tool_output(raw.content)             # lint/test 输出
        elif raw.output_format == "free_form":
            return extract_findings_via_llm(                  # Hermes skill 输出
                raw_text=raw.content,
                schema=FINDING_JSON_SCHEMA,
                prompt="Extract all review findings into the schema."
            )
```

这个归一化层让 CrossReview 可以消费任意形式的 reviewer 输出，不要求 reviewer 改变格式。

### 8.5 整体数据流

```
CrossReview 负责                           Hermes skill 负责
─────────────                              ─────────────────
policy 触发
    ↓
review_pack 构建  ←── 等价于 Hermes Steps 1-4
  (diff + evidence + acceptance criteria)
    ↓
reviewer orchestration ─────────────────→  SkillGuidedReviewer
                                             (加载 SKILL.md 程序)
                                             (构建 reviewer prompt)
                                             (isolated LLM session)  ←── 等价于 Hermes Step 5
                                             ↓
                        ←── RawReviewerOutput (自然语言)
    ↓
FindingNormalizer       ←── Hermes 没有这层
    ↓
adjudicator            ←── Hermes 没有这层
    ↓
verdict + findings
    ↓
review.md 写入         ←── Hermes 没有这层
    ↓
execution_gate 检查    ←── Hermes 没有这层
```

### 8.6 对 design.md 的影响

需要在 `design.md` 的以下章节补充：

1. **核心抽象 > 3. Reviewer** 章节：增加 `skill_guided` 作为第四种 reviewer 类型
2. **核心抽象 > 4. Finding** 章节：说明 `FindingNormalizer` 处理 free_form 输出的方式
3. **配置设计**：增加 `skill_path` 字段示例

→ **待合并进 design.md**（下一步操作）
