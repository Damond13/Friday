"""System Prompt 组装 — 注入用户记忆、知识、指令"""

from dataclasses import dataclass, field

BASE_SYSTEM_PROMPT = """你是 Friday，一个深度个人化的 AI 助手。你的特点：
- 你只属于当前用户，记住 TA 的偏好、习惯和纠正
- 像一个靠谱的搭档，主动、简洁、有用
- 用中文交流，除非用户明确要求其他语言"""


@dataclass
class PromptContext:
    """Prompt 上下文，包含需要注入的信息"""

    user_memories: list[str] = field(default_factory=list)
    knowledge: list[str] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)


def build_system_prompt(context: PromptContext | None = None) -> str:
    """组装完整 system prompt"""
    parts = [BASE_SYSTEM_PROMPT]

    if not context:
        return parts[0]

    if context.user_memories:
        parts.append("\n## 用户偏好与记忆")
        for mem in context.user_memories:
            parts.append(f"- {mem}")

    if context.knowledge:
        parts.append("\n## 相关知识")
        for k in context.knowledge:
            parts.append(f"- {k}")

    if context.instructions:
        parts.append("\n## 已学习的指令")
        for inst in context.instructions:
            parts.append(f"- {inst}")

    return "\n".join(parts)
