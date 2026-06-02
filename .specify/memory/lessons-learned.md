# Lessons Learned

## LL-001: spec-kit 初始化版本问题
- 日期: 2026-06-01
- 问题: spec-kit 新版用 skills/ 代替 commands/，PyPI 上的 speckit 包是光谱分析工具不是 spec-kit
- 影响: 安装错误包浪费时间
- 修复: 用 `uv tool install specify-cli` 安装正确的 CLI
- 规则: spec-kit 的 CLI 包名是 `specify-cli`，命令是 `specify init`

## LL-002: Understand-Anything 需要 pnpm 构建
- 日期: 2026-06-01
- 问题: 插件安装后 packages/core/dist/ 不存在，pnpm v11 需要手动 approve builds
- 影响: /understand 执行失败
- 修复: 全局安装 pnpm，手动 tsc 构建 core，运行 pnpm approve-builds
- 规则: Understand-Anything 安装后需先构建 core（`npx tsc` in packages/core/）

## LL-003: 智谱 API 限流
- 日期: 2026-06-01
- 问题: 并发 subagent 过多触发智谱 API 529 错误（访问量过大）
- 影响: batch 6-10 分析失败需重试
- 修复: 降低并发数，失败后重试
- 规则: 智谱 API 并发限制较严，大量 subagent 任务建议分批 3-5 个
