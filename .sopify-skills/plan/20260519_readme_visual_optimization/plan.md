# README 与文档视觉优化

level: light
服务蓝图: First-Use Adoption Proof（视觉资产缺口）
边界: 纯文档/视觉优化，不改 protocol / runtime / machine contract

## 目标

- 补齐 README 视觉资产（Adoption Proof 要求 ≥1 视觉资产展示核心工作流，架构图不计入）
- 解决 how-sopify-works 的 mermaid 图平台渲染兼容问题
- 降低 README 文字密度，提升首次访问者可读性

## 切片

### S1: 技术图表重绘（fireworks-tech-graph → SVG+PNG）

- [ ] 架构总览图 → `assets/sopify-architecture-v2.svg/.png`
- [ ] 主工作流图 → `assets/sopify-workflow.svg/.png`
- [ ] Checkpoint 暂停恢复图 → `assets/sopify-checkpoint.svg/.png`
- [ ] Plan 生命周期图 → `assets/sopify-plan-lifecycle.svg/.png`
- [ ] 知识层级图 → `assets/sopify-knowledge-layers.svg/.png`

### S2: 产品概念图（doc-to-sketch → PNG）

- [ ] README Cover（21:9）→ `assets/sopify-cover.png`
- [ ] "Why Sopify" 对比图（16:9）→ `assets/sopify-why.png`
- [ ] Quick Start 步骤图（16:9）→ `assets/sopify-quickstart-steps.png`

### S3: README 文案重构

- [ ] README.md 嵌入视觉资产 + 结构调整
- [ ] README.zh-CN.md 同步
- [ ] how-sopify-works.en.md / .md 渲染图替代 mermaid（mermaid 保留 `<details>` 折叠）
- [ ] `python3 scripts/check-readme-links.py` 通过

## 验收

- README 包含 ≥1 视觉资产展示核心工作流（非架构图）
- GitHub 渲染正常
- `check-readme-links.py` 通过
- 中英文 README 结构一致
