---
description: 按 fixplan 执行代码修复，遵守 Developer Agent 约束。
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Role Assignment: Developer

**You are operating as the Developer Agent.** 遵守以下约束：

- 只按 `fixplan.md` 中列出的改动清单修改代码
- 不扩大范围，不加无关优化
- 不自动 commit/push — 等用户明确指示
- 所有外部调用走 adapter 层
- 遵守 CLAUDE.md 中的编码规范

## Outline

1. **定位缺陷目录**：
   - 如果 `$ARGUMENTS` 指定了目录，使用它
   - 否则读取 `.specify/bugfix.json` 的 `bug_directory` 字段
   - 设置 `BUG_DIR` 为解析后的路径

2. **加载修复方案**：读取 `BUG_DIR/fixplan.md`

3. **执行修复**：
   - 按 fixplan 中的改动清单逐项执行
   - 每项改动完成后，简要报告改了什么
   - 如果执行中发现 fixplan 需要调整，暂停并告知用户

4. **检查改动范围**：
   - 确认实际改动没有超出 fixplan 的范围
   - 确认"不改动的部分"没有被误改
   - 确认相关测试是否需要同步更新（遵守 CLAUDE.md "测试同步维护" 规则）

5. **报告结果**：
   - 列出所有修改的文件和改动摘要
   - 标注是否有测试需要更新
   - 建议运行 `/bugfix.verify` 进行验证

## Key Rules

- **严格按 fixplan 执行**，不发挥、不加塞
- 如果发现 fixplan 有遗漏或错误，**暂停并报告**，不要自行决定
- 修改模块代码时，同步检查该模块的自动化测试是否需要更新
- 不自动运行测试（遵守 CLAUDE.md "禁止自动跑全量测试" 规则）

## Done When

- [ ] fixplan 中的所有改动项已执行
- [ ] 改动范围未超出 fixplan
- [ ] 测试更新需求已标注
- [ ] 修改摘要已报告给用户
- [ ] 已建议运行 `/bugfix.verify`
