"""工具定义 — Shell 执行、文件操作、知识库检索"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolDefinition:
    """工具定义，遵循 OpenAI function calling schema"""

    name: str
    description: str
    parameters: dict[str, Any]

    def to_openai_format(self) -> dict:
        """转换为 OpenAI function calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


# ── Shell 执行工具 ────────────────────────────────────

SHELL_EXECUTE = ToolDefinition(
    name="shell_execute",
    description="执行 Shell 命令并返回输出。安全命令（ls, cat, git）可直接执行，危险命令（rm, format）需用户确认。",
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要执行的 Shell 命令",
            },
            "timeout": {
                "type": "integer",
                "description": "超时秒数，默认 30",
                "default": 30,
            },
        },
        "required": ["command"],
    },
)

# ── 文件读取工具 ───────────────────────────────────────

FILE_READ = ToolDefinition(
    name="file_read",
    description="读取文件内容。支持文本文件，返回完整内容。",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "文件路径",
            },
            "offset": {
                "type": "integer",
                "description": "起始行号（从 0 开始）",
            },
            "limit": {
                "type": "integer",
                "description": "最大读取行数",
            },
        },
        "required": ["path"],
    },
)

# ── 文件写入工具 ───────────────────────────────────────

FILE_WRITE = ToolDefinition(
    name="file_write",
    description="写入内容到文件。会覆盖已有文件。",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "文件路径",
            },
            "content": {
                "type": "string",
                "description": "要写入的内容",
            },
        },
        "required": ["path", "content"],
    },
)

# ── 知识库检索工具 ──────────────────────────────────────

KNOWLEDGE_SEARCH = ToolDefinition(
    name="knowledge_search",
    description="从知识库中检索相关信息。支持关键词和语义搜索。",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索查询",
            },
            "limit": {
                "type": "integer",
                "description": "返回结果数量，默认 5",
                "default": 5,
            },
        },
        "required": ["query"],
    },
)


def get_tool_definitions() -> list[dict]:
    """返回所有可用工具的 function calling 定义"""
    tools = [SHELL_EXECUTE, FILE_READ, FILE_WRITE, KNOWLEDGE_SEARCH]
    return [t.to_openai_format() for t in tools]
