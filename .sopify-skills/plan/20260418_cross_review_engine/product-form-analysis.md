# CrossReview 独立产品形态分析

> **文档状态：已拍板方向**
> **Status**: Archived reference — 早期产品形态分析
> **当前事实源**: CrossReview 产品/发布事实以 `cross-review/.sopify-skills/plan/20260425_crossreview_product_master_plan/` 和 `cross-review/docs/v0-scope.md` 为准。
> **使用方式**: 本文只保留产品形态与边界分析，不参与当前 v0 / PyPI / Sopify Phase 4a 执行判断。
>
> 本文档定义 CrossReview 作为独立产品的交付形态、集成协议与边界。
> Sopify 是消费方之一，不是唯一宿主。

---

## 一、产品定位

CrossReview 是 **独立验证引擎**，解决"AI 不能可靠地审查自己的产出"这个工程问题。

核心管道：
```
Artifact → Review Pack → Reviewer(s) → Finding(s) → Adjudicator → Verdict → Policy Action
```

独立价值的来源不是"更多功能"，而是：
1. **清晰的输入协议**（ReviewPack） — 任何工具都能构造
2. **清晰的输出协议**（Finding/Verdict） — 任何工具都能消费
3. **零依赖的最小闭环** — 不需要 Sopify 也能跑

---

## 二、产品交付形态（5 个通道）

### 📦 形态 1: CLI（MVP 必须）

```bash
# 最小可用 — 在任何 git 仓库里
crossreview verify
# → 读 git diff, 自动构建 review pack, 运行 reviewer, 输出 findings

# 带 spec 对齐
crossreview verify --spec spec.md
# → 检查实现是否覆盖 spec 中的 acceptance criteria

# 多模型 review
crossreview verify --reviewers claude-sonnet,gpt-4o
# → 并发调用两个模型做独立审查

# CI 友好输出
crossreview verify --format json > review.json
crossreview verify --format sarif > review.sarif  # Phase 2
```

**独立价值**：`pip install crossreview && crossreview verify` 就能用。不需要知道 Sopify 是什么。

### 📦 形态 2: Python SDK（MVP 必须）

```python
from crossreview import Engine, ReviewPack, Artifact

pack = ReviewPack(
    artifact=Artifact.from_diff(diff_text),
    acceptance_criteria=["用户登录后应跳转到首页"],
    evidence={"tests": [{"command": "pytest", "status": "passed"}]},
)

engine = Engine(config_path="crossreview.yaml")
result = engine.review(pack)

print(result.verdict)      # "warn"
print(result.findings)     # [Finding(...), ...]
print(result.action)       # "review_required"
```

**独立价值**：任何 Python 工具通过 `import crossreview` 就能调用。这是被集成的核心通道。

### 📦 形态 3: MCP Server（Phase 1.5）

```yaml
tools:
  - crossreview_verify:
      description: "对工件进行独立验证审查"
      input: { artifact_kind, diff, acceptance_criteria, policy }
      output: { verdict, findings, action }

  - crossreview_configure:
      description: "配置 review 策略"
      input: { reviewers, policy }
```

**独立价值**：任何支持 MCP 的 AI agent（Claude Code, Cursor, Copilot, Gemini）都能直接调用。最具扩展性的通道。

### 📦 形态 4: Agent Skill（Phase 1.5）

```
# 以 SKILL.md 形式发布，可被放入任何 agent 的 skills 目录
skills/crossreview/
└── SKILL.md         # 程序性知识：如何使用 CrossReview 进行验证
```

**独立价值**：与 Hermes / Superpowers / HelloAgents 的 skill 生态兼容。

### 📦 形态 5: CI/CD 插件（Phase 2）

```yaml
# GitHub Action
- uses: crossreview/action@v1
  with:
    reviewers: claude-sonnet
    policy: strict
    spec: spec.md
```

---

## 三、集成协议：让消费方"零成本"接入

### 协议 = 3 个 JSON Schema

```
1. ReviewPack (输入)          → 消费方构造
2. ReviewResult (输出)        → CrossReview 产出
3. CrossReviewConfig (配置)   → 消费方提供
```

**每个消费方只需要做两件事**：
1. 把自己的上下文打包成 ReviewPack
2. 读取 ReviewResult 并决定如何反应

```
┌─────────────┐     ReviewPack      ┌──────────────┐     ReviewResult     ┌─────────────┐
│  Sopify     │──────────────────→  │  CrossReview  │──────────────────→  │  Sopify     │
│  spec-kit   │     (JSON)          │  Engine       │     (JSON)          │  spec-kit   │
│  hermes     │                     │               │                     │  hermes     │
│  superpowers│                     │               │                     │  superpowers│
│  helloagents│                     │               │                     │  helloagents│
│  CI/CD      │                     │               │                     │  CI/CD      │
└─────────────┘                     └──────────────┘                     └─────────────┘
   各自负责                           CrossReview                            各自负责
  "怎么打包"                          只负责                               "怎么反应"
                                    "验证 + 发现"
```

### 各消费方的 adapter 工作量预估

| 消费方 | 构造 ReviewPack | 消费 ReviewResult | 工作量 |
|-------|----------------|-------------------|-------|
| **Sopify** | 从 task + diff + evidence 打包 | verdict → handoff / checkpoint / review.md | 中 |
| **spec-kit** | 从 spec.md + generated code 打包 | verdict → gate step pass/reject | 小 |
| **superpowers** | 从 subagent output + spec 打包 | verdict → dispatch 下一步 | 小 |
| **hermes** | 从 delegate_task output 打包 | verdict → 决定是否 rollback | 小 |
| **helloagents** | 从 plan + code 打包 | verdict → delivery gate | 小 |
| **graphify** | 提供 graph_context 作为 evidence | 不直接消费（作为上游增强） | 小 |
| **CI/CD** | 从 git diff 打包 | verdict → PR comment / block merge | 小 |

---

## 四、独立产品的"Hello World"体验

开发者 3 分钟内应能感受到价值：

```bash
# 1. 安装
pip install crossreview

# 2. 配置 API key
export ANTHROPIC_API_KEY=sk-...

# 3. 在任何 git 仓库里，改完代码后：
crossreview verify

# 输出：
# ┌ CrossReview ──────────────────────────
# │ Verdict: warn
# │ Findings: 2
# │
# │ [HIGH] logic_regression
# │   Token refresh bypasses expiry check
# │   src/auth/token.ts:88
# │
# │ [MEDIUM] insufficient_tests
# │   No test covers the new error path
# │   src/api/handler.ts:42
# │
# │ Action: review_required
# └────────────────────────────────────────
```

不需要 Sopify。不需要 spec-kit。不需要配方案包。

---

## 五、产品边界

### CrossReview 负责的
- ✅ 验证协议（ReviewPack → Finding → Verdict）
- ✅ Reviewer 编排（fresh session / cross model / deterministic）
- ✅ 裁决逻辑（adjudicator）
- ✅ Policy 引擎（advisory / required / block）
- ✅ Report 生成（JSON / human-readable / SARIF）
- ✅ CLI + SDK + MCP Server

### CrossReview 不负责的
- ❌ 工作流编排（Sopify 的事）
- ❌ Spec 管理（spec-kit 的事）
- ❌ Plan 生命周期（Sopify 的事）
- ❌ Agent 调度（各宿主自己的事）
- ❌ PR/Git 平台集成（CI/CD 层的事）

---

## 六、MVP 仓库结构

```
cross-review/
├── crossreview/                 # Python package
│   ├── engine.py                # 核心引擎
│   ├── artifact.py              # Artifact 模型
│   ├── review_pack.py           # ReviewPack 构建
│   ├── reviewer/                # Reviewer 实现
│   │   ├── transport.py         # ReviewerTransport Protocol
│   │   ├── fresh_session.py     # 同模型新 session
│   │   ├── cross_model.py       # 跨模型
│   │   └── deterministic.py     # lint/test checker
│   ├── adjudicator.py           # 裁决逻辑
│   ├── finding.py               # Finding schema
│   ├── verdict.py               # Verdict schema
│   ├── policy.py                # Policy 引擎
│   ├── config.py                # 配置加载
│   └── report/                  # 输出格式
│       ├── json.py
│       ├── human.py
│       └── sarif.py             # Phase 2
├── cli/                         # CLI 入口
│   └── main.py                  # crossreview verify
├── mcp/                         # MCP Server（Phase 1.5）
│   └── server.py
├── profiles/                    # Review Profile（垂直能力）
│   ├── code_review.yaml
│   ├── design_review.yaml
│   └── final_audit.yaml
├── schemas/                     # JSON Schema 定义（集成协议）
│   ├── review_pack.schema.json
│   ├── review_result.schema.json
│   └── config.schema.json
├── tests/
├── pyproject.toml
├── crossreview.yaml.example     # 示例配置
└── README.md
```

---

## 七、外部产品集成分析：Graphify

### Graphify 是什么

Graphify 是一个 **代码知识图谱生成工具**：

```
代码/文档/PDF/截图 → tree-sitter AST + LLM 语义提取 → NetworkX 图 → Leiden 社区聚类
                                                                        ↓
输出: graph.json (可查询) + GRAPH_REPORT.md (概览) + graph.html (可视化)
```

核心能力：
- **25 种语言** 的确定性 AST 提取（类、函数、导入、调用图）
- **LLM 语义提取**（概念、关系、设计意图）
- **Leiden 社区发现**（基于图拓扑聚类，不用向量数据库）
- **置信度标签**：`EXTRACTED` / `INFERRED` / `AMBIGUOUS`
- **MCP Server**：暴露 `query_graph`, `get_node`, `get_neighbors`, `shortest_path` 给 AI agent

### 与 CrossReview 的 4 种集成模式

#### 🔗 模式 1: Evidence Provider（review pack 增强）

```
开发者改了 src/auth/token.ts
    ↓
CrossReview 构建 review pack 时，查询 graphify:
    graphify query "token auth" → 子图
    ↓
review_pack.evidence.graph_context = {
    "affected_nodes": ["TokenManager", "AuthFlow", "SessionStore"],
    "god_nodes_touched": ["AuthFlow"],       # 高连接度节点 = 高风险
    "communities_spanned": [2, 5],           # 跨社区 = 跨切面修改
    "ambiguous_relationships": ["TokenManager --?--> CacheLayer"]
}
```

**价值**：reviewer 不需要自己理解项目结构。graph 告诉它"这个改动涉及核心节点，跨了两个模块边界"。

#### 🔗 模式 2: Risk Signal（policy 触发增强）

```yaml
# crossreview.yaml 中的 graphify-aware policy
cross_review:
  policy:
    develop:
      required_when:
        - graphify_god_node_touched    # 改了核心节点 → 必须 review
        - graphify_cross_community     # 跨社区修改 → 必须 review
      advisory_when:
        - graphify_ambiguous_edge      # 涉及模糊关系 → 建议 review
```

**价值**：policy 不再只依赖静态 keyword（`auth`, `schema`），而是基于 **项目结构的动态分析** 做决策。

#### 🔗 模式 3: Reviewer Knowledge Base（reviewer 上下文注入）

```python
# CrossReview reviewer 执行前，注入 graphify 上下文
prompt = f"""
PROJECT STRUCTURE CONTEXT (from graphify):
{graph_report_summary}

God nodes (most connected entities): {god_nodes}
This change touches community {community_id}: {community_description}

REVIEW THE FOLLOWING DIFF:
{diff}
"""
```

**价值**：reviewer 在隔离上下文中仍然"懂项目"——不是靠 session 历史，而是靠结构化图谱。

#### 🔗 模式 4: Impact Analysis（变更影响分析）

```bash
# 变更影响分析作为 deterministic_checker 类型的 reviewer
crossreview verify --with-graphify
# → graphify 查询：从 changed files 出发，BFS 3 层
# → 输出：影响范围 + 是否触及核心路径 + 是否跨社区
# → 作为 deterministic finding 进入 adjudicator
```

**价值**：不需要 LLM 就能给出"这个改动的影响面有多大"的结构化评估。

### 集成接口设计

Graphify 已有 MCP Server（`serve.py`），CrossReview 通过 MCP 协议调用：

```
CrossReview                          Graphify MCP Server
    │                                      │
    ├── query_graph("auth flow") ─────────→│ → 子图文本
    ├── get_node("TokenManager") ─────────→│ → 节点详情
    ├── get_neighbors("AuthFlow") ────────→│ → 邻居 + 边
    └── shortest_path("A", "B") ──────────→│ → 路径
```

CrossReview 不需要直接依赖 graphify 的 Python API，通过 MCP 实现松耦合集成。

### 实现优先级

| 优先级 | 集成项 | Phase | 工作量 |
|-------|--------|-------|-------|
| 高 | `graphify_context` 作为 review_pack.evidence 可选字段 | 1.5 | 小 |
| 高 | `graphify_god_node_touched` 作为 policy 触发条件 | 2 | 中 |
| 中 | reviewer prompt 注入 GRAPH_REPORT.md 摘要 | 2 | 小 |
| 低 | graphify BFS 作为 deterministic_checker reviewer | 3 | 中 |

### 关键约束

1. **graphify 是可选依赖**：没有 graphify 的项目，CrossReview 正常工作
2. **通过 MCP 而非 import 集成**：保持两个产品的独立性
3. **graph.json 存在时自动增强**：检测到 `graphify-out/graph.json` → 自动注入 graph context

### 一句话总结

> Graphify 给 CrossReview 提供的是 **项目结构感知能力**——让 reviewer 不只是看 diff 本身，而是知道"这个 diff 在项目结构中意味着什么"。集成方式是通过 MCP Server 松耦合查询，不增加硬依赖。

---

## 八、本文档与方案包的关系

本文档定义了 CrossReview 的独立产品形态。后续 `design.md` 中的"独立使用形态"和"仓库形态"章节应以本文档为准更新。

与其他文档的关系：
- `background.md`：问题定义（为什么需要 CrossReview）
- `design.md`：核心架构（ReviewPack / Finding / Verdict / Policy 的技术细节）
- **本文档**：产品形态（如何交付、如何被集成）
- `cross-project-insights.md`：外部项目参考思想
- `hermes-insights.md`：Hermes 架构对比洞察
