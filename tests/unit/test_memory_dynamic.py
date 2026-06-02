"""动态记忆单元测试"""

import pytest

from friday.memory.dynamic import MemoryItem, MemorySearchResult


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

    def test_source_files(self) -> None:
        result = MemorySearchResult(source="files", content="decision", score=1.0)
        assert result.source == "files"


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

        deleted = delete_memory(item.id)
        assert deleted is True

    @pytest.mark.skip(reason="需要 LLM API 配置才能运行")
    def test_list_memories(self) -> None:
        from friday.memory.dynamic import add_memory, list_memories

        add_memory("测试记忆列表功能")
        items = list_memories()
        assert len(items) >= 1
