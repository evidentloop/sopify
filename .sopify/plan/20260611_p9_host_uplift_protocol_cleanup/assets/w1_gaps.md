# W1a Evidence & Gap Registry

> 本文件用途：W1a 三宿主冒烟的统一记录位置。每个单元（场景 × 宿主）一行，记录结果、gate check、反模式编号。
> 关联：`tasks.md` W1.6 / W1.7；`plan.md` W1a Acceptance。

---

## 一、7 场景业务 Prompt

### S1 · consult（直接回答，不接续 active plan）

```
解释 Sopify 的"单一写入入口"原则是什么意思？sopify_writer 和 sopify_contracts 分别负责什么？
```

**期望**：host 直接回答问题，不创建 plan，不写 state 文件。

**Gate B / C**：N/A — 无 plan 产出，不适用。

### S2 · quick_fix（单文件修复，不出 plan）

```
给 scripts/sopify_status.py 加一个 --quiet 参数：启用时不打印任何输出，只通过退出码反映状态（0=up_to_date 或 pinned_old_but_healthy，1=stale 或 broken）。
```

**期望**：host 定位文件、添加参数、产出 low-touch handoff（如有），不创建 plan。

**Gate B / C**：N/A — 无 plan 产出，不适用。

### S3 · light plan（3-5 文件，出 plan.md 单文件）

```
给 installer/hosts/ 下的 codex.py、claude.py、qoder.py、copilot.py 四个文件各补一段模块级 docstring，说明该宿主的 support_tier、entry mode 和关键特性。不改变现有代码逻辑。
```

**期望**：host 生成 light plan（仅 `plan.md`）。

**Gate A 文件清单**（level=light，来源 `protocol.md:73`）：
- [ ] `plan/<id>/plan.md` 存在

**Gate B 状态词一致**：plan.md 中 prose 使用的状态词须与文件顶部 Status 字段一致

**Gate C 开放问题核对**：plan.md 若有"开放问题"节，内容不得与任务描述矛盾

### S4 · standard plan（>5 文件，出 plan.md + tasks.md）

```
审计 Sopify 所有 Python 文件中的 import 语句，把相对 import 统一成绝对 import（以 sopify_writer / sopify_contracts / installer 为顶层包）。预计涉及 10+ 个文件。
```

**期望**：host 生成 standard plan（`plan.md` + `tasks.md`）。

**Gate A 文件清单**（level=standard，来源 `protocol.md:73`）：
- [ ] `plan/<id>/plan.md` 存在
- [ ] `plan/<id>/tasks.md` 存在

**Gate B 状态词一致**：plan.md 和 tasks.md 中 prose 使用的状态词须一致，且与各自文件顶部 Status 字段匹配

**Gate C 开放问题核对**：plan.md "开放问题"节与 tasks.md 中标记为 BLOCKED 的任务项不得矛盾

### S5 · 同宿主恢复（中断后重开同一宿主）

**准备步骤**：先让 host 开始 S3 的任务，在 host 写完 plan.md 但未执行时中断会话。

**恢复 prompt**：
```
我上次让你给 installer/hosts/ 四个适配器文件补模块级 docstring，你写了 plan 但还没开始执行。请继续。
```

**期望**：host 读取 `state/active_plan.json` → `plan/<id>/plan.md` → 接续执行，不重建 plan。

**Gate A 文件清单**（level=light，继承 S3）：
- [ ] `plan/<id>/plan.md` 存在（恢复后仍存在，未被覆盖或重建）

**Gate B 状态词一致**：恢复后 plan.md 状态词未被篡改或漂移到未定义值

**Gate C 开放问题核对**：恢复后 host 不得虚构新的"已完成"声明

### S6 · 跨宿主恢复（A 宿主写 → B 宿主续）

**准备步骤**：在 host A（如 Codex）中执行 S3，产出 plan.md + 至少 1 个 receipt。

**恢复 prompt（在 host B 如 Claude 中）**：
```
另一个宿主已经在 Sopify 项目里创建了一个 plan，要给 installer/hosts/ 四个适配器文件补模块级 docstring。请读取当前 state 和 plan，接着做没完成的部分。
```

**期望**：host B 读取 `state/active_plan.json` → `plan/<id>/plan.md` → `plan/<id>/receipts/`，消费 host A 的 evidence 后续接。

**Gate A 文件清单**（level=light，继承 S3）：
- [ ] `plan/<id>/plan.md` 存在（跨宿主读取后仍完整）
- [ ] `plan/<id>/receipts/` 存在且包含 host A 的 evidence

**Gate B 状态词一致**：host B 产出物中状态词须与 plan.md 已有状态字段一致

**Gate C 开放问题核对**：host B 不得忽略 host A 已登记的 BLOCKED 项或开放问题

### S7 · finalize（显式归档）

```
S3 的任务已经全部完成了。请执行 finalize：写 final receipt、归档到 history、清理 state、刷新蓝图索引。
```

**期望**：host 写 `receipts/final.json` → `history/<YYYY-MM>/<plan_id>/receipt.md` → 清 `state/active_plan.json` + `state/current_handoff.json` → 刷新 `blueprint/README.md`。

**Gate A 文件清单**（finalize 阶段，来源 `protocol.md:90` + `protocol.md:109`）：
- [ ] `plan/<id>/receipts/final.json` 存在且符合 `plan_receipt.schema.json`
- [ ] `history/<YYYY-MM>/<plan_id>/receipt.md` 存在且包含 outcome / summary / key_decisions
- [ ] `state/active_plan.json` 已删除
- [ ] `state/current_handoff.json` 已删除

**Gate B 状态词一致**：`receipt.md` 中 outcome 须与 `final.json` verdict 语义一致

**Gate C 开放问题核对**：归档时不得遗留未关闭的 BLOCKED 任务项（如有，须先 replan 或显式标记 deferred）

---

## 二、统一记录模板

每个单元填一行。W1.6 汇总时按此格式追加。

| 字段 | 说明 |
|------|------|
| scenario | S1 / S2 / S3 / S4 / S5 / S6 / S7 |
| host | Codex / Claude / Qoder / Copilot |
| verdict | PASS / FAIL / SKIP |
| gate_a_pkg | 包完整性：✓ / ✗ / NA（S1/S2 无 plan 产出时为 NA） |
| gate_b_status | 状态词一致：✓ / ✗ / NA |
| gate_c_open_q | 开放问题交叉核对：✓ / ✗ / NA |
| anti_pattern | 触发的反模式编号（A-G），无则填 none |
| gap_desc | 一句话描述 gap（FAIL 时必填，PASS 时可选） |

---

## 三、Evidence 记录区

> W1a 执行时在此追加。每个宿主一个子节。

### Codex

| scenario | host | verdict | gate_a_pkg | gate_b_status | gate_c_open_q | anti_pattern | gap_desc |
|----------|------|---------|------------|---------------|---------------|--------------|----------|
| S1 | Codex | | | | | | |
| S2 | Codex | | | | | | |
| S3 | Codex | PASS | ✓ | ✓ | ✓ | none | 一级工件保留在 assets/codex_s3_artifacts/，plan.md 含 8 canonical section，protocol_check PASS |
| S4 | Codex | PASS | ✓ | ✓ | ✓ | none | 一级工件保留在 assets/codex_s4_artifacts/，plan.md + tasks.md 均在，protocol_check PASS + tasks_file_check.json |
| S5 | Codex | PASS | ✓ | ✓ | ✓ | none | 一级工件保留在 assets/codex_s5_artifacts/；Session B 读取 Session A 同一 plan_id，plan.md sha256 一致，protocol_check continuation PASS |
| S6 | Codex | | | | | | |
| S7 | Codex | | | | | | |

### Claude

| scenario | host | verdict | gate_a_pkg | gate_b_status | gate_c_open_q | anti_pattern | gap_desc |
|----------|------|---------|------------|---------------|---------------|--------------|----------|
| S1 | Claude | | | | | | |
| S2 | Claude | | | | | | |
| S3 | Claude | | | | | | |
| S4 | Claude | | | | | | |
| S5 | Claude | | | | | | |
| S6 | Claude | | | | | | |
| S7 | Claude | | | | | | |

### Qoder

| scenario | host | verdict | gate_a_pkg | gate_b_status | gate_c_open_q | anti_pattern | gap_desc |
|----------|------|---------|------------|---------------|---------------|--------------|----------|
| S1 | Qoder | PASS | NA | NA | NA | none | 直接回答协议问题，无 plan/state 产出 |
| S2 | Qoder | PASS | NA | NA | NA | none | 实现 --quiet flag，测试通过，已回滚 |
| S3 | Qoder | PASS | ✓ | ✓ | ✓ | none | light plan 创建，3 gate 全过，已清理 |
| S4 | Qoder | PASS | ✓ | ✓ | ✓ | none | standard plan (plan.md+tasks.md) 创建，3 gate 全过，已清理 |
| S5 | Qoder | PASS | ✓ | ✓ | ✓ | none | Session A/B 真实分离，plan_id=20260617_host_docstrings 一致，plan.md 含 8 章节（含 Waves/Steps），verify_002.json continuation receipt 已写入；工件保留在 assets/qoder_s5_artifacts/ |
| S6 | Qoder | SKIP | — | — | — | — | 需要跨宿主（A 写 B 续），Qoder 单宿主无法测试；Codex surrogate 见 supplemental notes |
| S7 | Qoder | SKIP | — | — | — | — | 不能对 test plan 或活跃 P9 执行 finalize |
| W1.4a | Qoder | PASS | NA | NA | NA | none | 项目级 `.qoder/rules/` 与用户级 `~/.qoder/rules/` 均不存在，无覆盖机制生效 |

### Supplemental Notes

**Codex S6 surrogate continuation**：`receipts/verify_002.json` 证明 Codex 作为 host B 在 P9 active plan 上成功消费了 Qoder 的 verify_001.json 并完成 4 步协议入口链。这是 P9 plan 级别的跨宿主接续证据，不等同 w1_gaps.md S6 定义（S3 test plan → host B 续接，test plan 已清理）。

**Codex S5 same-host recovery**：`assets/codex_s5_session_a_artifacts/` 保留了 Session A 锚点，`assets/codex_s5_artifacts/` 保留了 Session B continuation 原始工件。`verify_002.json` 明确消费了 Session A 的 `active_plan.json` / `current_handoff.json` / `plan.md` / `exec_001.json`，并附带 `plan.md` sha256 一致性，`protocol_check_continuation.json` 为 PASS。该单元满足“两个真实 session + 同一 plan_id + 未覆盖原 plan”的 S5 PASS 口径。

**Qoder S5 same-plan-id recovery rehearsal**（superseded）：`assets/s5_artifacts/` 保留了 5 个原始工件（active_plan.json + current_handoff.json + plan.md + exec_001.json + verify_001.json），证明同一 plan_id 被读回且 plan.md 未被覆盖。但因同一对话内执行（非真正 session 中断）且 plan.md 缺 ## Waves / Steps（非合规 light plan），不满足最小清单 PASS 条件。已被下方 S5 PASS 证据取代。

**Qoder S5 same-host recovery PASS**：`assets/qoder_s5_artifacts/` 保留 3 个原始工件（Session A `state/active_plan.json` + `plan/20260617_host_docstrings/plan.md` + Session B `receipts/verify_002.json`）。Session A/B 为两个独立 Qoder session，Session B 读回同一 `plan_id=20260617_host_docstrings`，未重建 plan，从 Wave 1 执行到 Wave 3 完成。plan.md 含 8 必备章节（含 Waves/Steps），3 gate 全过。

**W1.4a Qoder rules precedence check**：已核验项目级 `.qoder/rules/`（不存在）与用户级 `~/.qoder/rules/`（不存在），当前 P9 workspace 未发现 rules 覆盖，也未发现其他已知更高优先的项目级入口。PASS（负向确认）。覆盖边界：本 PASS 仅限当前 P9 workspace；S5 临时 workspace 需重新核验 rules 覆盖面。

### Copilot（S1-S3 baseline smoke）

| scenario | host | verdict | gate_a_pkg | gate_b_status | gate_c_open_q | anti_pattern | gap_desc |
|----------|------|---------|------------|---------------|---------------|--------------|----------|
| S1 | Copilot | | | | | | |
| S2 | Copilot | | | | | | |
| S3 | Copilot | | | | | | |

---

## 四、Gap 分类区（W1.7）

> W1a 执行完毕后在此分类。

| gap_id | scenario | host | 类型 | 描述 | 修复归属 |
|--------|----------|------|------|------|---------|
| | | | 平台硬限制 / 可修 gap | | W2 / post-P9 |
