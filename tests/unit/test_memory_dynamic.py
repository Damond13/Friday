"""动态记忆单元测试"""

from pathlib import Path

import pytest

from friday.config import CONFIG_DIR
from friday.memory.dynamic import MemoryItem, MemorySearchResult, MEMORY_DIR


class TestMemoryItem:
    """MemoryItem 数据类"""

    def test_fields(self) -> None:
        item = MemoryItem(id="abc", content="test", metadata={"k": "v"}, score=0.9)
        assert item.id == "abc"
        assert item.content == "test"
        assert item.score == 0.9

    def test_defaults(self) -> None:
        item = MemoryItem(id="abc", content="test")
        assert item.metadata == {}
        assert item.score == 0.0


class TestMemorySearchResult:
    """MemorySearchResult 数据类"""

    def test_source_dynamic(self) -> None:
        result = MemorySearchResult(source="dynamic", content="test", score=0.8)
        assert result.source == "dynamic"
        assert result.content == "test"
        assert result.score == 0.8


class TestMemoryDir:
    """MEMORY_DIR 路径配置"""

    def test_memory_dir_under_config(self) -> None:
        assert MEMORY_DIR == CONFIG_DIR / "memory"

    def test_memory_dir_is_absolute(self) -> None:
        assert MEMORY_DIR.is_absolute()

    def test_memory_dir_name(self) -> None:
        assert MEMORY_DIR.name == "memory"


class TestSearchMemoryDegraded:
    """search_memory 降级行为"""

    def test_returns_list_on_failure(self) -> None:
        from friday.memory.dynamic import search_memory
        from unittest.mock import patch

        with patch("friday.memory.dynamic._get_memory", return_value=None):
            results = search_memory("test query")
            assert isinstance(results, list)
            assert len(results) == 0

    def test_returns_memory_search_result_type(self) -> None:
        from friday.memory.dynamic import search_memory
        from unittest.mock import patch

        mock_result = MemorySearchResult(
            source="dynamic", content="用户偏好Python", score=0.9
        )
        with patch("friday.memory.dynamic._get_memory", return_value=None):
            results = search_memory("Python")
            assert isinstance(results, list)
            for item in results:
                assert isinstance(item, MemorySearchResult)


class TestMem0Integration:
    """Mem0 集成测试（需要 LLM 配置，标记为可选）"""

    @pytest.mark.skip(reason="需要 LLM API 配置才能运行")
    def test_add_and_search(self) -> None:
        from friday.memory.dynamic import add_memory, search_memory, delete_memory

        item = add_memory("用户偏好暗色主题")
        assert item.id != ""
        assert item.content == "用户偏好暗色主题"

        results = search_memory("颜色偏好")
        assert len(results) >= 1
        assert all(isinstance(r, MemorySearchResult) for r in results)

        deleted = delete_memory(item.id)
        assert deleted is True

    @pytest.mark.skip(reason="需要 LLM API 配置才能运行")
    def test_list_memories(self) -> None:
        from friday.memory.dynamic import add_memory, list_memories

        add_memory("测试记忆列表功能")
        items = list_memories()
        assert len(items) >= 1
