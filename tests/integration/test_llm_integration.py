"""集成测试 — LLM 调用（需要 API 连接）"""

import pytest

from tests.integration.conftest import requires_llm
from friday.llm import (
    chat,
    chat_stream,
    get_current_model,
    get_current_provider,
    LLMResponse,
)
from friday.llm.prompts import PromptContext, build_system_prompt
from friday.llm.tools import get_tool_definitions


@requires_llm
class TestLLMChat:
    """LLM 基础对话"""

    def test_basic_chat(self) -> None:
        """基础对话返回非空回复"""
        resp = chat([{"role": "user", "content": "说'测试通过'两个字"}])
        assert isinstance(resp, LLMResponse)
        assert resp.content
        assert "测试通过" in resp.content

    def test_chat_returns_usage(self) -> None:
        """对话返回 token 使用统计"""
        resp = chat([{"role": "user", "content": "你好"}])
        assert resp.usage.total_tokens > 0
        assert resp.usage.prompt_tokens > 0
        assert resp.usage.completion_tokens > 0

    def test_multi_turn_conversation(self) -> None:
        """多轮对话保持上下文"""
        messages = [
            {"role": "user", "content": "记住我的名字叫 TestUser123"},
            {"role": "assistant", "content": "好的，TestUser123。"},
            {"role": "user", "content": "我叫什么名字？只回答名字"},
        ]
        resp = chat(messages)
        assert "TestUser123" in resp.content


@requires_llm
class TestLLMStream:
    """LLM 流式对话"""

    def test_stream_yields_tokens(self) -> None:
        """流式返回多个 token"""
        tokens = list(chat_stream([{"role": "user", "content": "说'流式测试通过'"}]))
        assert len(tokens) > 0
        full = "".join(tokens)
        assert "流式测试通过" in full

    def test_stream_concatenation(self) -> None:
        """流式 token 拼接后为完整回复"""
        tokens = []
        for token in chat_stream([{"role": "user", "content": "说 hello，只回答这一个词"}]):
            tokens.append(token)
        full = "".join(tokens)
        assert len(full) > 0
        assert any(kw in full.lower() for kw in ("hello", "你好")), f"回复未包含预期内容: {full}"


@requires_llm
class TestLLMWithContext:
    """LLM 带 PromptContext 对话"""

    def test_context_injection(self) -> None:
        """PromptContext 注入后 LLM 能感知上下文"""
        ctx = PromptContext(
            user_memories=["用户最喜欢的语言是 RustTestLang"],
            knowledge=[],
            instructions=[],
        )
        resp = chat(
            [{"role": "user", "content": "我最喜欢什么语言？只回答语言名"}],
            context=ctx,
        )
        assert "RustTestLang" in resp.content

    def test_knowledge_injection(self) -> None:
        """知识注入后 LLM 能引用"""
        ctx = PromptContext(
            user_memories=[],
            knowledge=["XYZ星球是虚构的，位于仙女座星系"],
            instructions=[],
        )
        resp = chat(
            [{"role": "user", "content": "XYZ星球在哪里？只回答位置"}],
            context=ctx,
        )
        assert "仙女座" in resp.content

    def test_instruction_injection(self) -> None:
        """指令注入后 LLM 遵守"""
        ctx = PromptContext(
            user_memories=[],
            knowledge=[],
            instructions=["回答必须以 [END] 结尾"],
        )
        resp = chat(
            [{"role": "user", "content": "说一句话"}],
            context=ctx,
        )
        assert resp.content.strip().endswith("[END]")


@requires_llm
class TestLLMToolCalling:
    """LLM 工具调用"""

    def test_tool_definitions_format(self) -> None:
        """工具定义格式正确"""
        tools = get_tool_definitions()
        assert len(tools) == 4
        names = [t["function"]["name"] for t in tools]
        assert "shell_execute" in names
        assert "file_read" in names
        assert "file_write" in names
        assert "knowledge_search" in names

    def test_tool_call_triggered(self) -> None:
        """LLM 正确生成工具调用"""
        tools = get_tool_definitions()
        resp = chat(
            [{"role": "user", "content": "请用 shell 执行 echo tool_test_ok 命令"}],
            tools=tools,
        )
        assert len(resp.tool_calls) > 0
        tc = resp.tool_calls[0]
        assert tc.name == "shell_execute"
        assert "echo" in tc.arguments.get("command", "")

    def test_provider_and_model(self) -> None:
        """获取当前 provider 和 model"""
        provider = get_current_provider()
        model = get_current_model()
        assert provider
        assert model
