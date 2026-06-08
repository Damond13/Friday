"""executors.py 单元测试 — knowledge_add 执行器边界场景

注：部分测试实际写入文件系统（通过 adapter.add_note），属集成测试性质。"""

import asyncio

import pytest

from friday.llm.executors import get_executor


@pytest.fixture
def knowledge_add():
    return get_executor("knowledge_add")


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestKnowledgeAddExecutor:
    def test_empty_title_returns_error(self, knowledge_add):
        result = _run(knowledge_add({"title": "", "content": "内容"}))
        assert not result.success
        assert "title" in result.output

    def test_empty_content_returns_error(self, knowledge_add):
        result = _run(knowledge_add({"title": "标题", "content": ""}))
        assert not result.success
        assert "content" in result.output

    def test_long_title_truncated(self, knowledge_add):
        long_title = "A" * 150
        result = _run(knowledge_add({"title": long_title, "content": "内容"}))
        assert result.success
        assert "已添加笔记" in result.output
        assert "标题已截断" in result.output

    def test_successful_add(self, knowledge_add):
        result = _run(knowledge_add({
            "title": "测试笔记",
            "content": "这是一条测试笔记",
            "tags": ["测试"],
        }))
        assert result.success
        assert "已添加笔记" in result.output
        assert "测试笔记" in result.output

    def test_whitespace_only_title_returns_error(self, knowledge_add):
        result = _run(knowledge_add({"title": "   ", "content": "内容"}))
        assert not result.success

    def test_whitespace_only_content_returns_error(self, knowledge_add):
        result = _run(knowledge_add({"title": "标题", "content": "   "}))
        assert not result.success
