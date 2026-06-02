"""adapter 统一接口单元测试"""

from pathlib import Path

import pytest

from friday.instruction import adapter
from friday.instruction.models import InstructionType


@pytest.fixture
def isolated(tmp_path: Path) -> None:
    """隔离指令目录并清除缓存"""
    from friday.instruction import store

    old_dir = store.INSTRUCTIONS_DIR
    store.INSTRUCTIONS_DIR = tmp_path
    adapter._invalidate_cache()
    yield
    store.INSTRUCTIONS_DIR = old_dir
    adapter._invalidate_cache()


class TestTeachValidation:
    """teach() 参数验证"""

    def test_trigger_too_short(self, isolated: None) -> None:
        with pytest.raises(ValueError, match="触发词"):
            adapter.teach(name="x", trigger="a", actions=[{"command": "echo"}])

    def test_trigger_empty(self, isolated: None) -> None:
        with pytest.raises(ValueError, match="触发词"):
            adapter.teach(name="x", trigger="", actions=[{"command": "echo"}])

    def test_actions_empty(self, isolated: None) -> None:
        with pytest.raises(ValueError, match="动作列表"):
            adapter.teach(name="x", trigger="test", actions=[])

    def test_action_missing_command(self, isolated: None) -> None:
        with pytest.raises(ValueError, match="command"):
            adapter.teach(name="x", trigger="test", actions=[{"desc": "no cmd"}])

    def test_conditional_without_description(self, isolated: None) -> None:
        with pytest.raises(ValueError, match="description"):
            adapter.teach(
                name="x",
                trigger="test",
                actions=[{"command": "echo"}],
                type="conditional",
            )


class TestTeachWorkflow:
    """teach() 工作流类型推断"""

    def test_single_action_defaults_to_single(self, isolated: None) -> None:
        instr = adapter.teach(
            name="deploy", trigger="deploy", actions=[{"command": "./deploy.sh"}]
        )
        assert instr.type == InstructionType.SINGLE

    def test_multi_action_auto_workflow(self, isolated: None) -> None:
        instr = adapter.teach(
            name="release",
            trigger="release",
            actions=[
                {"command": "pytest"},
                {"command": "deploy.sh"},
            ],
        )
        assert instr.type == InstructionType.WORKFLOW

    def test_explicit_type_preserved(self, isolated: None) -> None:
        instr = adapter.teach(
            name="release",
            trigger="release",
            actions=[{"command": "pytest"}, {"command": "deploy.sh"}],
            type="workflow",
        )
        assert instr.type == InstructionType.WORKFLOW


class TestMatch:
    """match() 匹配与 top_k"""

    def test_match_returns_results(self, isolated: None) -> None:
        adapter.teach(name="deploy", trigger="deploy", actions=[{"command": "./deploy.sh"}])
        results = adapter.match("帮我 deploy")
        assert len(results) == 1
        assert results[0].score == 1.0

    def test_match_top_k_limits_results(self, isolated: None) -> None:
        adapter.teach(name="a", trigger="alpha", actions=[{"command": "echo a"}])
        adapter.teach(name="b", trigger="beta", actions=[{"command": "echo b"}])
        adapter.teach(name="c", trigger="charlie", actions=[{"command": "echo c"}])
        results = adapter.match("alpha", top_k=1)
        assert len(results) <= 1


class TestRemove:
    """remove() 删除"""

    def test_remove_existing(self, isolated: None) -> None:
        adapter.teach(name="deploy", trigger="deploy", actions=[{"command": "./deploy.sh"}])
        assert adapter.remove("deploy") is True
        assert adapter.match("deploy") == []

    def test_remove_nonexistent(self, isolated: None) -> None:
        assert adapter.remove("nonexistent") is False


class TestReload:
    """reload() 重新加载"""

    def test_reload_returns_count(self, isolated: None) -> None:
        adapter.teach(name="a", trigger="alpha", actions=[{"command": "echo"}])
        adapter.teach(name="b", trigger="beta", actions=[{"command": "echo"}])
        count = adapter.reload()
        assert count == 2
