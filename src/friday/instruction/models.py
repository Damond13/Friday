"""指令学习模块 — 数据模型定义"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class InstructionType(Enum):
    """指令类型"""

    SINGLE = "single"
    WORKFLOW = "workflow"
    CONDITIONAL = "conditional"


@dataclass
class Action:
    """指令中的单个操作步骤"""

    command: str
    description: str = ""
    confirm: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "description": self.description,
            "confirm": self.confirm,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Action":
        return cls(
            command=data["command"],
            description=data.get("description", ""),
            confirm=data.get("confirm", False),
        )


@dataclass
class Instruction:
    """一条用户教会 Friday 的操作规则"""

    name: str
    trigger: str
    actions: list[Action]
    type: InstructionType = InstructionType.SINGLE
    description: str = ""
    keywords: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "trigger": self.trigger,
            "type": self.type.value,
            "description": self.description,
            "keywords": self.keywords,
            "actions": [a.to_dict() for a in self.actions],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Instruction":
        return cls(
            name=data["name"],
            trigger=data["trigger"],
            type=InstructionType(data.get("type", "single")),
            description=data.get("description", ""),
            keywords=data.get("keywords", []),
            actions=[Action.from_dict(a) for a in data["actions"]],
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


@dataclass
class MatchResult:
    """匹配接口的返回值"""

    instruction: Instruction
    score: float
    match_type: str
