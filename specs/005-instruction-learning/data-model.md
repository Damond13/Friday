# Data Model: 指令学习模块

**Date**: 2026-06-02 | **Branch**: `005-instruction-learning`

## Entities

### Instruction

指令实体，存储在 YAML 文件中。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | str | 是 | 指令名称，用于显示和标识 |
| trigger | str | 是 | 触发词/短语，用于匹配用户输入 |
| type | InstructionType | 是 | 指令类型：single/workflow/conditional |
| description | str | 否 | 指令描述 |
| keywords | list[str] | 否 | 额外匹配关键词 |
| actions | list[Action] | 是 | 动作列表（至少 1 个） |
| created_at | str | 是 | ISO 格式创建时间 |
| updated_at | str | 是 | ISO 格式更新时间 |

**验证规则**:
- trigger 非空且长度 ≥ 2 字符
- actions 至少包含 1 个 Action
- type 必须是 single/workflow/conditional 之一

### Action

指令中的单个操作步骤。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| command | str | 是 | 执行内容（shell 命令） |
| description | str | 否 | 步骤描述 |
| confirm | bool | 否 | 是否需要确认，默认 false |

**验证规则**:
- command 非空

### MatchResult

匹配接口的返回值。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| instruction | Instruction | 是 | 匹配到的指令 |
| score | float | 是 | 匹配度评分 0.0~1.0 |
| match_type | str | 是 | 匹配类型："exact" / "keyword" |

## Enumerations

### InstructionType

| 值 | 说明 |
|----|------|
| single | 单步指令：1 个 action |
| workflow | 多步工作流：多个 action 按顺序执行 |
| conditional | 条件分支：具体分支逻辑由 LLM 层解析 |

## Entity Relationships

```
Instruction 1──* Action
MatchResult *──1 Instruction
```

- 一个 Instruction 包含 1~N 个 Action
- 一次匹配查询返回 0~N 个 MatchResult

## Storage Mapping

```
~/.friday/instructions/
├── deploy.yaml              # Instruction{name="deploy", type=single, actions=[...]}
├── check-disk.yaml          # Instruction{name="check disk", type=single, actions=[...]}
└── release.yaml             # Instruction{name="release", type=workflow, actions=[...]}
```

每个 YAML 文件对应一条 Instruction，文件名 = slug(trigger).yaml。
