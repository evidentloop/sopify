---
plan_id: 20260323_readme-about-changelog
feature_key: readme-about-changelog
level: standard
lifecycle_state: archived
knowledge_sync:
  project: skip
  background: review
  design: required
  tasks: review
archive_ready: true
---

# 任务清单: README / About / CHANGELOG 对外表达收口

## Step 1 — 冻结文档职责边界

- [x] 1.1 按 `design.md` 的 "Section → Destination 映射" 逐段确认迁出去向，冻结清单（完成标准：映射表已确认，无待定项）
- [x] 1.2 固定“public README / workflow docs / maintainer docs (CONTRIBUTING) / blueprint contract”四层职责边界；仅 workflow 文档使用 `docs/`，不承接 `skill-authoring` 迁移
- [x] 1.3 明确本包不包含 `AI Co-Authorship`、`positioning.md`、Superpowers 对比说明、AGENTS.md/CLAUDE.md 模板化

## Step 2 — 重写 public README

- [x] 2.1 重写 `README.md`，保留头部 badge / 语言切换 / 版本契约，正文切回"价值主张 + 工作流 + 快速开始"，**正文 ≤250 行**
- [x] 2.2 同步重写 `README_EN.md`，保持与中文 `##` 级标题结构一致
- [x] 2.3 按 Section → Destination 映射，将内部 contract / checkpoint / bundle 维护细节迁出到 CONTRIBUTING 或 blueprint
- [x] 2.4 保留目录体系、FAQ、命令速查，但只保留面向用户的必要信息
- [x] 2.5 删除"与 HelloAGENTS 的区别"段落（README.md:725-737 及 README_EN.md 对应段落）
- [x] 2.6 精简"文件说明"段落，只保留顶层目录结构 + `docs/` 一行，并添加对应语言的 workflow 文档链接
- [x] 2.7 调整顶部贡献入口：`README.md` 指向 `CONTRIBUTING_CN.md`，`README_EN.md` 指向 `CONTRIBUTING.md`
- [x] 2.8 在“核心特性”与“快速开始”之间增加 1 段极短 design rationale，不单独起标题；中文链接 `docs/how-sopify-works.md`，英文链接 `docs/how-sopify-works.en.md`

## Step 3 — 新增 workflow 文档

- [x] 3.1 新建 `docs/how-sopify-works.md`，包含图 1（主工作流）、图 2（checkpoint）、图 4（目录结构）与图 3 附录
- [x] 3.2 新建 `docs/how-sopify-works.en.md`，与中文 workflow 文档保持相同 `##` 结构
- [x] 3.3 按设计固定图语义：图 1 先路由后做代码任务复杂度分流；图 2 的 `confirm_execute` 放在开发前；图 4 显式展示 `state/sessions/<session_id>/...`
- [x] 3.4 在中英文 workflow 文档增加 `Harness Engineering` 设计来源节：四行映射表 + 1 段短说明 + 1 条 OpenAI 官方外链
- [x] 3.5 不映射 `Agent Cross-Review`，避免在 public 文档中超出 Sopify 当前真实能力边界

## Step 4 — 收口维护者与长期文档

- [x] 4.1 将 runtime bundle / smoke / sync / Skill Authoring 稳定规范迁入 `CONTRIBUTING.md`（EN）
- [x] 4.2 新建 `CONTRIBUTING_CN.md`，与 `CONTRIBUTING.md` 保持 `##` 标题结构一致，内容允许翻译差异
- [x] 4.3 将 `CONTRIBUTING.md:12` 的 `skill-authoring` 死链改为 `Codex/Skills/{CN,EN}/skills/sopify/` 目录链接
- [x] 4.4 将长期偏好预载入、文档治理约定、KB 职责矩阵、checkpoint 各段说明与分层试点材料迁入 `.sopify-skills/blueprint/design.md`
- [x] 4.5 按 `design.md` 的三档文案产出 GitHub About 建议（CN/EN tagline + short description + repo description + topics），在 plan 中记录为手工更新步骤
- [x] 4.6 明确 GitHub About 三档文案保持 outcome-first，不引入 `Harness Engineering` 字样

## Step 5 — 优化 CHANGELOG 草稿模板

- [x] 5.1 改造 `scripts/release-draft-changelog.py` 的 `render_draft()`，按语义区域输出 Docs / Runtime / Scripts / Skills / Tests / Changed 六类 section 与动作描述
- [x] 5.2 更新 `tests/test_release_hooks.py` 中 `test_release_draft_changelog_populates_empty_unreleased` 等断言，验证新的区域 section 名和动作描述
- [x] 5.3 验证 `scripts/release-sync.sh` / `scripts/check-version-consistency.sh` 不受影响

## Step 6 — 新增 README 验收脚本

- [x] 6.1 新建 `scripts/check-readme-links.py`，覆盖：badge 版本一致性、页内锚点有效性、语言切换链接、CN/EN `##` 标题结构对齐、相对文件链接存在性、README 正文行数限制（随内容增加限制也会动态变化？）
- [x] 6.2 验证脚本在当前 README 改版后能通过，并按当前文件所在目录解析 `./` / `../` 路径

## 验证清单

- [x] V1 `python3 -m unittest tests/test_release_hooks.py -v` 通过
- [x] V2 `bash scripts/check-version-consistency.sh` 通过
- [x] V3 `python3 scripts/check-readme-links.py` 通过（覆盖 badge / 锚点 / 语言切换 / 相对链接 / README ≤250 行）
- [x] V4 手动确认 `[Unreleased]` 草稿不再只是文件列表
- [x] V4a 验证只变更 2 种区域时，draft 只出现对应 2 个 section（无空区域泄漏）
- [x] V5 确认 `README.md` / `README_EN.md` 分别链接到对应语言的 workflow 文档与贡献入口
- [x] V6 确认 `CONTRIBUTING.md` 与 `CONTRIBUTING_CN.md` 的 `##` 标题结构一致（不要求内容级完全一致）
- [x] V7 确认 `docs/how-sopify-works.md` / `.en.md` 的 `##` 标题结构一致
