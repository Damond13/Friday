---
description: 创建结构化缺陷报告，采集问题现象、环境信息和复现步骤。
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

1. **生成缺陷短名**：从用户描述中提取 2-4 个关键词，生成 kebab-case 短名（如 `search-empty-result`、`startup-crash`）

2. **创建缺陷目录**：
   - 扫描 `bugs/` 目录，确定下一个可用编号（三位数字，如 `001`、`002`）
   - 创建 `bugs/<编号>-<短名>/` 目录
   - 将目录路径写入 `.specify/bugfix.json` 的 `bug_directory` 字段

3. **采集缺陷信息**：根据用户描述，补充以下信息（用户未提供的，标注 [待确认]）：
   - 现象描述
   - 环境信息（操作系统、Python 版本、Friday 版本）
   - 复现步骤
   - 期望行为 vs 实际行为
   - 影响范围
   - 严重程度（P1 阻塞 / P2 重要 / P3 一般）

4. **生成 bug-report.md**：使用 `.specify/templates/bug-report-template.md` 模板，填充采集的信息

5. **展示草稿**：将生成的 bug-report.md 展示给用户，等待确认或修改

6. **确认后写入**：用户确认后写入 `bugs/<编号>-<短名>/bug-report.md`

## Key Rules

- 严重程度默认 P2，除非用户明确说明或现象明显是阻塞级
- 用户未提供的环境信息，主动询问（如"这个问题在什么系统上出现的？"）
- 复现步骤必须具体、可操作，不要模糊描述
- 每份报告只记录一个缺陷，多个问题拆分多份

## Done When

- [ ] 缺陷目录已创建
- [ ] `.specify/bugfix.json` 已更新
- [ ] `bug-report.md` 已写入并经用户确认
- [ ] 报告缺陷编号和目录路径给用户
