# 变更提案: README / About / CHANGELOG 对外表达收口

## 需求背景

当前仓库已经进入“自用 + 二次接入”阶段，但根目录文档仍然明显偏内部实现视角：

- `README.md` 当前约 **830+ 行**、`README_EN.md` 体量相当，大量内部 contract / checkpoint / bundle 细节挤占新用户入口
- `CONTRIBUTING.md` 当前不足 **50 行** 且仅有英文，一旦维护者内容迁入会严重失衡，且中文用户无法参考
- GitHub About 只说“准备建议文案”，缺少可直接复制的 CN/EN 分档产物
- `scripts/release-draft-changelog.py` 的 `render_draft()` 只做 tests / non-tests 二分法，CHANGELOG 条目全是 “Updated release-relevant files”，对读者没有信息量
- 当前 plan 缺少可落地的“段落 → 目标文件”映射产物，执行时仍需要临场决策
- README 验收项中 badge / 锚点 / 语言切换 / CN-EN 结构对齐全靠手工检查，容易回归
- 目前还没有单独的 workflow 说明文档，新用户很难快速理解 `.sopify-skills/`、checkpoint 与 plan 生命周期之间的关系
- `CONTRIBUTING.md` 里对 `docs/skill-authoring*.md` 的引用目前是死链，需要改回现有真源入口
- “与 HelloAGENTS 的区别”段落面向内部，新用户不理解 HelloAGENTS 是什么

这类问题共享同一目标：把“外部用户 first”的叙事收回来，同时不破坏 release 相关自动化。

评分:
- 方案质量: 9/10
- 落地就绪: 9/10

评分理由:
- 优点: 范围集中在 public README、workflow 文档、维护者文档、release draft 与轻量验证脚本，输出物明确；职责边界、触发逻辑与验收口径已经收口，执行路径稳定。
- 扣分: GitHub About 仍属于仓库外手工步骤；README / workflow / CONTRIBUTING 三组双语文档会带来持续维护成本。

## 变更内容

1. 将 `README.md` / `README_EN.md` 改成面向新用户的推广入口与工作流说明，正文 **≤250 行**
2. 新增 `docs/how-sopify-works.md` / `docs/how-sopify-works.en.md` 作为 workflow 说明文档，承接 Mermaid 流程图与 `.sopify-skills/` 目录详解
3. 落成“Section → Destination”文档职责矩阵作为正式设计产物
4. 将维护者内容迁入 `CONTRIBUTING.md`（EN）+ `CONTRIBUTING_CN.md`（CN）双文件，并把 `skill-authoring` 死链改回现有真源目录
5. 将需要长期保留的 contract、治理说明与分层试点材料迁入 `.sopify-skills/blueprint/design.md`
6. 产出 GitHub About 的 CN/EN tagline + short description + repo description 三档文案
7. 优化 `scripts/release-draft-changelog.py`，把 `[Unreleased]` 草稿改为按语义区域分组并输出动作化描述
8. 新增 `scripts/check-readme-links.py` 自动化 README 验收（badge / 锚点 / 语言切换 / 相对链接 / 行数）
9. 删除 README 中“与 HelloAGENTS 的区别”段落，并将“文件说明”收口为精简目录树 + workflow 文档链接
10. README 仅增加一段极短的 harness design rationale；GitHub About 保持 outcome-first，不引入 Harness 术语
11. 在 workflow 文档中补“Harness Engineering → Sopify”映射节，仅放 1 条 OpenAI 官方参考链接，不把二手材料带入 public README
12. 将与本目标无关的附加项留在 backlog，不继续绑进主执行链路

## 非目标

- 不调整 runtime gate 行为
- 不触碰 `runtime/models.py` / `tests/test_runtime.py` 结构拆分
- 不在本包中落地 `AI Co-Authorship`、`positioning.md`、Superpowers 对比说明
- 不优化 AGENTS.md / CLAUDE.md 模板化（单独立项）
- 不为 `skill-authoring` 迁移额外创建 `docs/skill-authoring*.md`
- 不把 `Harness Engineering` 作为 README 首屏或 GitHub About 的主定位

## 影响范围

- 模块: `.sopify-skills/blueprint/design.md`
- 新增文件: `CONTRIBUTING_CN.md`, `docs/how-sopify-works.md`, `docs/how-sopify-works.en.md`, `scripts/check-readme-links.py`
- 修改文件: `README.md`, `README_EN.md`, `CONTRIBUTING.md`, `scripts/release-draft-changelog.py`, `tests/test_release_hooks.py`

## 风险评估

- 风险: README / workflow 文档 / CONTRIBUTING 三组文档在改版后发生链接失效或中英文结构漂移。
- 缓解: 保留头部 badge / 版本契约；新增 `scripts/check-readme-links.py` 做结构化验证；对 `CONTRIBUTING.md` / `CONTRIBUTING_CN.md` 只要求 `##` 标题结构对齐，不做内容级 diff；README 将 Harness 限定为 1 段 design rationale，避免主叙事重新内化；执行 `tests/test_release_hooks.py` 与 `scripts/check-version-consistency.sh` 做回归验证。
