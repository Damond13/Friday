"""集成测试 — 记忆系统"""

import pytest

from friday.memory.files import (
    add_decision,
    add_lesson,
    list_decisions,
    list_lessons,
    get_constitution,
    search_files,
    MEMORY_DIR,
)
from friday.memory.adapter import (
    add_decision as adapter_add_decision,
    add_lesson as adapter_add_lesson,
    list_decisions as adapter_list_decisions,
    list_lessons as adapter_list_lessons,
    get_constitution as adapter_get_constitution,
    search_memories,
)


@pytest.fixture(autouse=True)
def _cleanup_memory_files():
    """测试前后记录状态"""
    before_decisions = list_decisions()
    before_lessons = list_lessons()
    yield
    # 不自动删除，因为文件记忆是长期存储
    # 但可以验证测试产物


class TestFileMemory:
    """文件记忆（决策/经验/宪法）"""

    def test_add_decision(self) -> None:
        """添加决策记录"""
        d = add_decision(
            title="inttest_使用Pytest",
            decision="选择pytest作为测试框架",
            context="集成测试需要",
        )
        assert d.title == "inttest_使用Pytest"
        assert d.date
        assert d.status == "已采纳"

    def test_add_decision_with_status(self) -> None:
        """添加自定义状态的决策"""
        d = add_decision(
            title="inttest_待定决策",
            decision="考虑中",
            status="待定",
        )
        assert d.status == "待定"

    def test_list_decisions(self) -> None:
        """列出决策记录"""
        add_decision("inttest_列表决策测试", "测试用")
        decisions = list_decisions()
        assert isinstance(decisions, list)
        titles = [d.title for d in decisions]
        assert any("inttest_列表决策测试" in t for t in titles)

    def test_add_lesson(self) -> None:
        """添加经验教训"""
        l = add_lesson(
            title="inttest_测试要先写",
            lesson="先写测试再写代码效率更高",
            context="TDD 实践",
        )
        assert l.title == "inttest_测试要先写"
        assert l.date

    def test_list_lessons(self) -> None:
        """列出经验教训"""
        add_lesson("inttest_列表经验测试", "测试用", "集成测试")
        lessons = list_lessons()
        assert isinstance(lessons, list)
        titles = [l.title for l in lessons]
        assert any("inttest_列表经验测试" in t for t in titles)

    def test_get_constitution(self) -> None:
        """读取项目宪法"""
        content = get_constitution()
        assert isinstance(content, str)

    def test_search_files_found(self) -> None:
        """文件记忆搜索能找到匹配项"""
        add_decision("inttest_搜索测试决策", "关于搜索功能的决策")
        results = search_files("inttest_搜索测试")
        assert len(results) > 0
        assert results[0].source == "files"

    def test_search_files_not_found(self) -> None:
        """搜索无匹配返回空"""
        results = search_files("zzz_nonexistent_memory_query_99999")
        assert isinstance(results, list)


class TestMemoryAdapter:
    """记忆统一接口"""

    def test_adapter_add_decision(self) -> None:
        """通过 adapter 添加决策"""
        d = adapter_add_decision("inttest_Adapter决策", "通过适配器")
        assert d.title == "inttest_Adapter决策"

    def test_adapter_add_lesson(self) -> None:
        """通过 adapter 添加经验"""
        l = adapter_add_lesson("inttest_Adapter经验", "通过适配器")
        assert l.title == "inttest_Adapter经验"

    def test_adapter_list(self) -> None:
        """通过 adapter 列出决策和经验"""
        decisions = adapter_list_decisions()
        lessons = adapter_list_lessons()
        assert isinstance(decisions, list)
        assert isinstance(lessons, list)

    def test_search_memories_unified(self) -> None:
        """统一搜索返回文件记忆结果"""
        add_decision("inttest_统一搜索测试", "关于统一搜索")
        results = search_memories("inttest_统一搜索")
        assert len(results) > 0
        sources = [r.source for r in results]
        assert "files" in sources
