"""记忆上下文注入单元测试"""

from unittest.mock import patch

import pytest

from friday.cli.session import Session, Message
from friday.llm.prompts import PromptContext


class TestBuildContextQuery:
    """_build_context 使用用户消息内容检索"""

    def test_uses_user_message_as_query(self) -> None:
        from friday.cli.repl import _build_context

        session = Session(messages=[Message(role="user", content="帮我写个Python脚本")])
        with patch("friday.memory.adapter.search_memories", return_value=[]) as mock_search:
            _build_context(session)
            mock_search.assert_called_once_with("帮我写个Python脚本", limit=5)

    def test_not_use_hardcoded_keywords(self) -> None:
        from friday.cli.repl import _build_context

        session = Session(messages=[Message(role="user", content="今天天气怎么样")])
        with patch("friday.memory.adapter.search_memories", return_value=[]) as mock_search:
            _build_context(session)
            call_args = mock_search.call_args
            assert call_args[0][0] != "用户偏好 习惯 设置"
            assert call_args[0][0] == "今天天气怎么样"

    def test_empty_session_returns_empty_context(self) -> None:
        from friday.cli.repl import _build_context

        session = Session(messages=[])
        result = _build_context(session)
        assert result.user_memories == []

    def test_empty_message_returns_empty_context(self) -> None:
        from friday.cli.repl import _build_context

        session = Session(messages=[Message(role="user", content="   ")])
        result = _build_context(session)
        assert result.user_memories == []


class TestBuildContextLimit:
    """记忆注入上限和过滤"""

    def test_max_5_memories(self) -> None:
        from friday.cli.repl import _build_context
        from friday.memory.dynamic import MemorySearchResult

        results = [
            MemorySearchResult(source="dynamic", content=f"记忆{i}", score=0.9)
            for i in range(8)
        ]
        session = Session(messages=[Message(role="user", content="测试")])
        with patch("friday.memory.adapter.search_memories", return_value=results):
            ctx = _build_context(session)
            assert len(ctx.user_memories) <= 5

    def test_filters_low_score(self) -> None:
        from friday.cli.repl import _build_context
        from friday.memory.dynamic import MemorySearchResult

        results = [
            MemorySearchResult(source="dynamic", content="高相关", score=0.8),
            MemorySearchResult(source="dynamic", content="低相关", score=0.1),
            MemorySearchResult(source="dynamic", content="中等", score=0.3),
        ]
        session = Session(messages=[Message(role="user", content="测试")])
        with patch("friday.memory.adapter.search_memories", return_value=results):
            ctx = _build_context(session)
            assert "高相关" in ctx.user_memories
            assert "中等" in ctx.user_memories
            assert "低相关" not in ctx.user_memories

    def test_all_low_score_returns_empty(self) -> None:
        from friday.cli.repl import _build_context
        from friday.memory.dynamic import MemorySearchResult

        results = [
            MemorySearchResult(source="dynamic", content=f"低{i}", score=0.1)
            for i in range(3)
        ]
        session = Session(messages=[Message(role="user", content="测试")])
        with patch("friday.memory.adapter.search_memories", return_value=results):
            ctx = _build_context(session)
            assert ctx.user_memories == []


class TestBuildContextDegraded:
    """检索异常时降级"""

    def test_exception_returns_empty_context(self) -> None:
        from friday.cli.repl import _build_context

        session = Session(messages=[Message(role="user", content="测试")])
        with patch("friday.memory.adapter.search_memories", side_effect=RuntimeError("Mem0 不可用")):
            ctx = _build_context(session)
            assert ctx.user_memories == []
            assert isinstance(ctx, PromptContext)
