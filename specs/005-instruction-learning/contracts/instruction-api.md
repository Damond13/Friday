# API Contract: instruction 模块公共接口

**Module**: `friday.instruction`
**Entry Point**: `adapter.py`

## 公共 API

### teach(name, trigger, actions, type, description, keywords) → Instruction

创建一条新指令并保存到 YAML 文件。

**Parameters**:
- `name: str` — 指令名称
- `trigger: str` — 触发词（长度 ≥ 2）
- `actions: list[dict[str, Any]]` — 动作列表，每个 dict 包含 command(str), description(str|None), confirm(bool)
- `type: str` — 指令类型："single" / "workflow" / "conditional"，默认 "single"
- `description: str | None` — 描述
- `keywords: list[str] | None` — 额外匹配关键词

**Returns**: `Instruction` — 创建的指令对象

**Raises**:
- `ValueError` — trigger 为空或长度 < 2，actions 为空

**Example**:
```python
from friday.instruction import teach, match, list_instructions, remove

# 创建单步指令
instr = teach(
    name="deploy",
    trigger="deploy",
    actions=[{"command": "./deploy.sh"}],
)

# 创建多步工作流
instr = teach(
    name="发版",
    trigger="发版",
    actions=[
        {"command": "pytest", "description": "跑测试"},
        {"command": "build.sh", "description": "构建"},
        {"command": "deploy.sh", "description": "部署"},
    ],
    type="workflow",
    keywords=["release", "发布"],
)
```

---

### match(text, top_k) → list[MatchResult]

匹配用户输入文本到已知指令。

**Parameters**:
- `text: str` — 用户输入文本
- `top_k: int` — 返回最多 N 条结果，默认 5

**Returns**: `list[MatchResult]` — 按匹配度降序排列

**Match Types**:
- `"exact"` — trigger 完全出现在输入中，score = 1.0
- `"keyword"` — 关键词部分匹配，score = 0.0~1.0

**Example**:
```python
results = match("帮我 deploy 一下")
# [MatchResult(instruction=Instruction(name="deploy"), score=1.0, match_type="exact")]

results = match("看看磁盘")
# [MatchResult(instruction=Instruction(name="check disk"), score=0.6, match_type="keyword")]
```

---

### list_instructions() → list[Instruction]

列出所有已保存的指令，按名称排序。

**Returns**: `list[Instruction]`

---

### remove(name) → bool

删除指定名称的指令。

**Parameters**:
- `name: str` — 指令名称

**Returns**: `bool` — 是否成功删除（False 表示不存在）

---

### reload() → int

重新从文件系统加载所有指令文件。

**Returns**: `int` — 成功加载的指令数量

## 类型导出

从 `friday.instruction` 可直接导入的类型：

- `Instruction` — 指令数据类
- `Action` — 动作数据类
- `MatchResult` — 匹配结果数据类
- `InstructionType` — 指令类型枚举
