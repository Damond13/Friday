"""指令管理工具定义 — instruction_add/search/list/delete"""

from dataclasses import dataclass
from typing import Any


@dataclass
class _ToolDef:
    name: str
    description: str
    parameters: dict[str, Any]

    def to_openai_format(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


INSTRUCTION_ADD = _ToolDef(
    name="instruction_add",
    description="教会 Friday 一条新指令。用户说「以后每次我说 X，你就做 Y」时使用。",
    parameters={
        "type": "object",
        "properties": {
            "trigger": {"type": "string", "description": "触发词，如「部署」「上线」"},
            "actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "要执行的命令"},
                        "description": {"type": "string", "description": "命令说明"},
                        "confirm": {"type": "boolean", "description": "是否需要用户确认"},
                    },
                    "required": ["command"],
                },
                "description": "动作列表",
            },
            "name": {"type": "string", "description": "指令名称（可选，默认用触发词）"},
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "额外关键词（可选，提升匹配率）",
            },
        },
        "required": ["trigger", "actions"],
    },
)

INSTRUCTION_SEARCH = _ToolDef(
    name="instruction_search",
    description="语义检索已学指令。用自然语言搜索，能匹配近义词。",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索查询"},
            "limit": {"type": "integer", "description": "返回结果数量，默认 5", "default": 5},
        },
        "required": ["query"],
    },
)

INSTRUCTION_LIST = _ToolDef(
    name="instruction_list",
    description="列出所有已学指令的名称和触发词。",
    parameters={"type": "object", "properties": {}, "required": []},
)

INSTRUCTION_DELETE = _ToolDef(
    name="instruction_delete",
    description="删除一条已学指令。",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "要删除的指令名称"},
        },
        "required": ["name"],
    },
)
