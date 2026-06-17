---
title: Add module-level docstrings to host adapter files
plan_id: w1a_s5_host_docstrings
status: draft
level: light
created: 2026-06-13
owner: qoder
---

# Add Module-Level Docstrings to Host Adapter Files

## Context / Why

`installer/hosts/` 下 4 个宿主适配器文件（codex.py, claude.py, qoder.py, copilot.py）当前只有常量注册和 import，缺少模块级 docstring。需要为每个文件补充 docstring 说明该宿主的 support_tier、entry mode 和关键特性。

## Scope

- `installer/hosts/codex.py`：补模块级 docstring
- `installer/hosts/claude.py`：补模块级 docstring
- `installer/hosts/qoder.py`：补模块级 docstring
- `installer/hosts/copilot.py`：补模块级 docstring

不修改任何现有代码逻辑，仅添加 docstring。

## Approach

1. 读取每个文件的 `HostAdapter` 常量定义
2. 基于常量值编写 docstring（support_tier 从 `installer/hosts/base.py` 和 `installer/models.py` 推断）
3. 在每个文件顶部（import 之前）插入 docstring
4. 跑测试确认无回归

## Key Decisions

- docstring 内容基于已有常量，不引入新字段
- 使用 Python triple-quote 格式，符合 PEP 257

## Constraints / Not-in-scope

- 不改 HostAdapter dataclass 定义
- 不改 base.py
- 不添加新代码逻辑

## Status / Progress

- [ ] codex.py docstring
- [ ] claude.py docstring
- [ ] qoder.py docstring
- [ ] copilot.py docstring
- [ ] 测试验证

## Next

按列表顺序逐项添加。
