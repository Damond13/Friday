"""指令执行器单元测试 — instruction_add/search/list/delete 边界场景"""

import asyncio

import pytest

from friday.llm.executors import get_executor


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture
def instruction_add():
    return get_executor("instruction_add")


@pytest.fixture
def instruction_search():
    return get_executor("instruction_search")


@pytest.fixture
def instruction_list():
    return get_executor("instruction_list")


@pytest.fixture
def instruction_delete():
    return get_executor("instruction_delete")


class TestInstructionAdd:
    def test_empty_trigger_returns_error(self, instruction_add):
        result = _run(instruction_add({"trigger": "", "actions": [{"command": "ls"}]}))
        assert not result.success
        assert "trigger" in result.output

    def test_empty_actions_returns_error(self, instruction_add):
        result = _run(instruction_add({"trigger": "部署", "actions": []}))
        assert not result.success
        assert "actions" in result.output

    def test_successful_add(self, instruction_add):
        result = _run(instruction_add({
            "trigger": "测试指令",
            "actions": [{"command": "echo hello", "description": "打印"}],
            "name": "测试指令",
            "keywords": ["测试"],
        }))
        assert result.success
        assert "已学会指令" in result.output


class TestInstructionSearch:
    def test_empty_query_returns_error(self, instruction_search):
        result = _run(instruction_search({"query": ""}))
        assert not result.success
        assert "query" in result.output

    def test_search_returns_results(self, instruction_search, instruction_add):
        _run(instruction_add({
            "trigger": "部署搜索测试",
            "actions": [{"command": "git push"}],
            "keywords": ["deploy"],
        }))
        result = _run(instruction_search({"query": "部署搜索测试"}))
        assert result.success


class TestInstructionList:
    def test_list_returns_success(self, instruction_list):
        result = _run(instruction_list({}))
        assert result.success


class TestInstructionDelete:
    def test_empty_name_returns_error(self, instruction_delete):
        result = _run(instruction_delete({"name": ""}))
        assert not result.success
        assert "name" in result.output

    def test_delete_nonexistent(self, instruction_delete):
        result = _run(instruction_delete({"name": "不存在的指令"}))
        assert not result.success
        assert "未找到" in result.output
