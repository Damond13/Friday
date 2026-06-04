"""LLM 模块共用数据类型"""

from dataclasses import dataclass, field


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: TokenUsage = field(default_factory=TokenUsage)


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_call_id: str
    success: bool
    output: str


@dataclass
class AgentResult:
    """Agent 循环最终结果"""
    reply: str
    messages: list[dict] = field(default_factory=list)
    tool_calls_count: int = 0
