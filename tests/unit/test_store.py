"""store.py 单元测试 — 笔记文件管理"""

import pytest
from pathlib import Path

from friday.knowledge.store import (
    Note, SearchResult, create_note_file, read_note_file,
    delete_note_file, list_note_files, generate_note_id,
)
import friday.knowledge.store as store_mod


class TestNote:
    def test_to_markdown(self) -> None:
        note = Note(id="abc123", title="测试", content="你好世界", tags=["t1"], created_at="2026-01-01")
        md = note.to_markdown()
        assert "id: abc123" in md
        assert "title: 测试" in md
        assert "tags: [t1]" in md
        assert "你好世界" in md

    def test_from_markdown(self) -> None:
        text = "---\nid: abc\ntitle: 标题\ntags: [py, ai]\ncreated_at: 2026-01-01\n---\n\n正文内容\n"
        note = Note.from_markdown(text, Path("/tmp/test.md"))
        assert note.id == "abc"
        assert note.title == "标题"
        assert note.tags == ["py", "ai"]
        assert note.content == "正文内容"

    def test_from_markdown_no_tags(self) -> None:
        text = "---\nid: abc\ntitle: 标题\n---\n\n正文\n"
        note = Note.from_markdown(text, Path("/tmp/test.md"))
        assert note.tags == []

    def test_roundtrip(self) -> None:
        note = Note(id="xyz", title="RT", content="内容", tags=["a"], created_at="2026-06-01")
        md = note.to_markdown()
        restored = Note.from_markdown(md, Path("/tmp/rt.md"))
        assert restored.id == note.id
        assert restored.title == note.title
        assert restored.content == note.content
        assert restored.tags == note.tags


class TestSearchResult:
    def test_defaults(self) -> None:
        r = SearchResult()
        assert r.score == 0.0
        assert r.source == ""


class TestFileOps:
    def test_create_and_read(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(store_mod, "NOTES_DIR", tmp_path)
        note = Note(id="f1", title="文件测试", content="测试内容")
        path = create_note_file(note)
        assert path.exists()
        read = read_note_file(path)
        assert read.id == "f1"
        assert read.content == "测试内容"

    def test_delete(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(store_mod, "NOTES_DIR", tmp_path)
        note = Note(id="f2", title="删除测试", content="内容")
        create_note_file(note)
        assert delete_note_file("f2")

    def test_delete_nonexistent(self) -> None:
        assert not delete_note_file("aabbccdd")

    def test_delete_invalid_id(self) -> None:
        import pytest as pt
        with pt.raises(ValueError, match="无效的 note_id"):
            delete_note_file("../../etc/passwd")

    def test_list(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(store_mod, "NOTES_DIR", tmp_path)
        create_note_file(Note(id="l1", title="A", content="a"))
        create_note_file(Note(id="l2", title="B", content="b"))
        files = list_note_files()
        assert len(files) == 2


class TestHelpers:
    def test_generate_note_id(self) -> None:
        assert len(generate_note_id()) == 8
