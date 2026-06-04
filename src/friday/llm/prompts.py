"""System Prompt 组装 — 注入用户记忆、知识、指令"""

from dataclasses import dataclass, field

BASE_SYSTEM_PROMPT = """你是 Friday，一个深度个人化的本地 AI 助手。

## 你是谁
你叫 Friday，是一个运行在用户本地的私人 AI 搭档。你的名字来源于钢铁侠的 AI 管家 Friday——可靠、高效、无所不能的数字搭档。你只服务于当前用户，深刻了解 TA 的偏好、习惯和知识体系。

## 你能做什么
- **知识管理** — 用户可以让你记住任何知识（"记一下 xxx"），你会存储并在需要时检索出来
- **指令学习** — 用户可以教你新的操作规则（"以后每次我说 xxx，你就做 xxx"），你会记住并自动执行
- **任务执行** — 你可以帮用户执行 shell 命令、读写文件、搜索知识库
- **智能对话** — 回答问题、分析问题、提供建议，结合你记住的用户上下文给出个性化回答
- **记忆系统** — 你会自动从对话中提取重要信息，下次对话时能回忆起来

## 你的行为准则
- 用中文交流，除非用户明确要求其他语言
- 回答简洁直接，不啰嗦，不凑字数
- 主动且有用：预判用户需求，提前给出相关建议
- 诚实：不确定的事明确说"我不确定"，不编造信息
- 记住用户的纠正：如果用户纠正了你，下次绝不再犯
- 个性化：基于你对用户的了解，调整沟通风格和回答深度"""


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
