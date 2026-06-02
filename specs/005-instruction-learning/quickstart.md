# Quickstart: 指令学习模块验证场景

**Date**: 2026-06-02 | **Branch**: `005-instruction-learning`

以下 5 个场景按优先级排列，验证指令学习模块的核心功能。

## 场景 1: 创建单步指令

```python
from friday.instruction import teach, match

# 教学
instr = teach(
    name="deploy",
    trigger="deploy",
    actions=[{"command": "./deploy.sh"}],
)

# 验证
assert instr.name == "deploy"
assert instr.type == "single"
assert len(instr.actions) == 1

# 匹配验证
results = match("帮我 deploy 一下")
assert len(results) == 1
assert results[0].match_type == "exact"
assert results[0].score == 1.0
```

## 场景 2: 创建多步工作流

```python
from friday.instruction import teach, match

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

# 验证
assert instr.type == "workflow"
assert len(instr.actions) == 3
assert instr.actions[0].command == "pytest"
```

## 场景 3: 关键词模糊匹配

```python
from friday.instruction import teach, match

teach(name="check disk", trigger="检查磁盘空间",
      actions=[{"command": "df -h"}], keywords=["磁盘", "disk", "空间"])

# 精确匹配
results = match("检查磁盘空间")
assert any(r.match_type == "exact" for r in results)

# 关键词匹配
results = match("看看磁盘")
assert len(results) > 0
assert results[0].match_type == "keyword"
```

## 场景 4: 指令管理

```python
from friday.instruction import teach, list_instructions, remove

teach(name="test1", trigger="test1", actions=[{"command": "echo 1"}])
teach(name="test2", trigger="test2", actions=[{"command": "echo 2"}])

# 列表
all_instrs = list_instructions()
assert len(all_instrs) >= 2

# 删除
removed = remove("test1")
assert removed is True

# 验证删除
results = match("test1")
assert len(results) == 0
```

## 场景 5: YAML 文件直接编辑

```python
import yaml
from pathlib import Path
from friday.instruction import teach, reload, match

teach(name="build", trigger="build", actions=[{"command": "make"}])

# 手动修改 YAML 文件
yaml_path = Path.home() / ".friday" / "instructions" / "build.yaml"
with open(yaml_path) as f:
    data = yaml.safe_load(f)
data["actions"][0]["command"] = "make prod"
with open(yaml_path, "w") as f:
    yaml.dump(data, f, allow_unicode=True)

# 重新加载并验证
count = reload()
assert count >= 1

results = match("build")
assert results[0].instruction.actions[0].command == "make prod"
```
