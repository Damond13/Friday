# 根因诊断: 工具调用输出显示混乱

**日期**: 2026-06-07 | **缺陷来源**: [bug-report.md](./bug-report.md)

## 根因分析

### 直接原因

两个显示函数的设计未考虑长内容场景：

1. **`show_tool_call`**（`display.py:82-85`）：用 `" ".join(f"{k}={v!r}"...)` 拼接所有参数。当 `shell_execute` 的 `command` 是多行 Python 脚本时，`!r` 将换行转为字面 `\n`，输出变成几百字符的单行。

2. **`show_tool_result`**（`display.py:88-94`）：用 `output[:200].replace("\n", " ")` 处理结果。将所有换行替换为空格后截断 200 字符，文件内容、YAML 等结构化输出完全丧失可读性。

### 根本原因

两个函数在 Agent 工具调用功能（spec 007）中首次实现时，仅考虑了简单场景（短命令、短结果），未对长内容和多行内容做显示优化。属于设计遗漏，不是架构缺陷。

## 调研发现

### 开源社区同类问题

| 来源 | 内容 |
|------|------|
| [Gemini CLI](https://geminicli.com/docs/reference/configuration/) | 提供可配置的工具输出截断阈值，超长内容自动截断 |
| [hermes-agent#16520](https://github.com/NousResearch/hermes-agent/issues/16520) | 同类 AI Agent 工具输出截断 bug，需在显示层处理 |
| [Evil Martians CLI UX](https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays) | CLI 进度显示 UX 最佳实践，推荐有意义的截断 |

### 改进方案对比

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| 截断参数值 | 对每个参数值截断到 N 字符，超出显示 `...` | 简单，一视同仁 | 可能丢失关键信息 |
| 按参数类型截断 | `command` 截断到 80 字符，其他参数保持 | 针对性强 | 需要了解各工具参数含义 |
| 只显示首行 | 多行内容只显示第一行 + `...` | 保留结构感 | 可能丢失关键信息 |

**推荐方案**: 截断参数值到 80 字符（单行），结果保留换行但限制行数（最多 3 行），总长度限制 200 字符。

## 问题分级

- [x] **代码级 bug** — 现有方案正确，只是显示逻辑不够好 → 进入 fixplan
- [ ] **方案级问题** — 当前方案选型有根本性缺陷 → 建议转入 SDD 新功能流程重新设计

## 诊断结论

两个显示函数缺少长内容截断逻辑，改进 `show_tool_call` 和 `show_tool_result` 的截断策略即可修复。
