"""watcher.py 单元测试 — 文件监控事件处理"""

from pathlib import Path
from unittest.mock import patch, MagicMock

from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileDeletedEvent

from friday.knowledge.watcher import _KnowledgeHandler, _is_supported


class TestIsSupported:
    def test_md_file(self) -> None:
        assert _is_supported(Path("test.md"))

    def test_txt_file(self) -> None:
        assert _is_supported(Path("test.txt"))

    def test_unsupported_extension(self) -> None:
        assert not _is_supported(Path("test.pdf"))

    def test_hidden_file(self) -> None:
        assert not _is_supported(Path(".hidden.md"))


class TestKnowledgeHandler:
    def setup_method(self) -> None:
        self.handler = _KnowledgeHandler()

    def test_on_created_calls_index(self) -> None:
        event = FileCreatedEvent(src_path="/tmp/notes/test.md")
        with patch("friday.knowledge.watcher._index_file") as mock_index:
            self.handler.on_created(event)
        mock_index.assert_called_once_with(Path("/tmp/notes/test.md"))

    def test_on_created_ignores_unsupported(self) -> None:
        event = FileCreatedEvent(src_path="/tmp/notes/test.pdf")
        with patch("friday.knowledge.watcher._index_file") as mock_index:
            self.handler.on_created(event)
        mock_index.assert_not_called()

    def test_on_modified_calls_reindex(self) -> None:
        event = FileModifiedEvent(src_path="/tmp/notes/test.md")
        with patch("friday.knowledge.watcher._reindex_file") as mock_reindex:
            self.handler.on_modified(event)
        mock_reindex.assert_called_once_with(Path("/tmp/notes/test.md"))

    def test_on_deleted_calls_remove(self) -> None:
        event = FileDeletedEvent(src_path="/tmp/notes/test.md")
        with patch("friday.knowledge.watcher._remove_index") as mock_remove:
            self.handler.on_deleted(event)
        mock_remove.assert_called_once_with(Path("/tmp/notes/test.md"))
