---
description: 根因诊断 — 定位问题根因，调研开源方案，判断代码级还是方案级问题。
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **定位缺陷目录**：
   - 如果 `$ARGUMENTS` 指定了目录，使用它
   - 否则读取 `.specify/bugfix.json` 的 `bug_directory` 字段
   - 设置 `BUG_DIR` 为解析后的路径

2. **加载缺陷报告**：读取 `BUG_DIR/bug-report.md`

3. **代码定位**：
   - 根据 bug-report 中的现象描述和复现步骤，定位相关代码文件和函数
   - 使用 CodeGraph 或 grep 追踪代码路径
   - 记录涉及的文件路径和行号

4. **根因分析**：
   - 分析直接原因（哪行代码/哪个条件触发了 bug）
   - 分析根本原因（为什么会写出这样的代码 — 设计缺陷、遗漏、假设错误等）
   - 检查是否存在同类问题的风险（其他地方是否有相同模式）

5. **强制调研**（关键步骤）：
   - 使用 WebSearch 搜索开源社区是否有同类问题和解决方案
   - 搜索关键词：`[相关技术] + [问题关键词] + bug/issue`
   - 如果是架构级问题，搜索同类软件的解决方案（如"终端集成 webview vs electron"）

6. **问题分级判断**：
   - **代码级 bug**：当前方案正确，只是实现有缺陷 → 进入 fixplan
   - **方案级问题**：方案选型本身有根本性缺陷 → 建议转入 SDD 新功能流程

7. **生成 diagnosis.md**：使用 `.specify/templates/diagnosis-template.md` 模板，填充分析结果

8. **展示草稿**：将诊断结果展示给用户，等待确认

9. **确认后写入**：用户确认后写入 `BUG_DIR/diagnosis.md`

## Key Rules

- **必须做调研**，不能只看代码就下结论。至少搜索 2-3 个相关关键词
- 区分"直接原因"和"根本原因" — 不能只停留在表面
- 如果判断为方案级问题，明确说明为什么当前方案不可修复，以及推荐的新方案
- 涉及的每个文件和函数都要引用具体路径和行号

## Done When

- [ ] 根因分析完成，区分了直接原因和根本原因
- [ ] 开源调研已完成
- [ ] 问题分级判断已做出（代码级 / 方案级）
- [ ] `diagnosis.md` 已写入并经用户确认
