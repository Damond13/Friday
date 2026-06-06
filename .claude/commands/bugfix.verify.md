---
description: 验证缺陷修复有效性，检查无回归问题。
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

2. **加载上下文**：读取 `BUG_DIR/bug-report.md`、`diagnosis.md`、`fixplan.md`

3. **验证修复有效性**：
   - 按 bug-report 中的复现步骤，验证问题是否已解决
   - 如果 bug 是特定平台/环境的，记录验证环境并标注未验证的平台
   - 如果无法在当前环境复现原 bug，说明验证局限性

4. **回归检查**：
   - 检查修复是否影响了相关功能（参考 diagnosis 中标注的影响范围）
   - 检查 fixplan 中"不改动的部分"是否保持不变
   - 如果修改了公共接口或共享模块，评估对其他模块的影响

5. **代码质量检查**（轻量级）：
   - 改动是否符合 CLAUDE.md 编码规范（文件大小、函数大小、类型注解）
   - 是否引入了新的安全隐患
   - 是否有冗余代码（修复过程中的临时代码是否清理干净）

6. **测试更新确认**：
   - 确认 fixplan 中标注的测试更新已在 fix 阶段完成
   - 如果 fixplan 标注"暂无自动化测试"，确认跳过合理
   - 如发现测试遗漏，在验证报告中标注

7. **生成验证报告**：在 `BUG_DIR/verify-report.md` 中记录：
   - 验证环境
   - 修复有效性结论
   - 回归检查结论
   - 测试更新确认
   - 未验证项（如有）
   - 后续建议（如需要特定平台验证）

8. **更新 bug-report 状态**：将 bug-report.md 状态更新为"已验证"

## Key Rules

- 如果无法完全验证（如特定平台 bug），诚实标注局限性，不要声称已验证
- 回归检查重点关注 fixplan 中标注的影响范围
- 如果发现新问题，建议创建新的 `/bugfix.report` 而非在当前修复中扩大范围

## Done When

- [ ] 修复有效性已验证（或标注了验证局限性）
- [ ] 回归检查已完成
- [ ] 代码质量检查已完成
- [ ] 测试更新已确认
- [ ] `verify-report.md` 已写入
- [ ] 结果已报告给用户
