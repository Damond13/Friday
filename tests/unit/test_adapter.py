"""knowledge/adapter.py 单元测试 — 统一检索接口"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import friday.knowledge.store as store_mod
import friday.knowledge.vector as vector_mod
from friday.knowledge.adapter import (
    add_note, delete_note, search, rag_query, _deduplicate, _build_context,
)
from friday.knowledge.store import SearchResult


@pytest.fixture(autouse=True)
def _reset_vector():
    vector_mod.reset_client()
    yield
    vector_mod.reset_client()


class TestAddNote:
    def test_creates_note_with_index(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(store_mod, "NOTES_DIR", tmp_path)
        with patch("friday.knowledge.adapter.ensure_vector"), \
             patch("friday.knowledge.adapter.vector.upsert"):
            note = add_note("测试标题", "测试内容", tags=["test"])
        assert note.id
        assert note.title == "测试标题"
        assert note.content == "测试内容"
        assert note.tags == ["test"]
        assert (tmp_path / f"{note.id}.md").exists()


class TestDeleteNote:
    def test_deletes_note(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(store_mod, "NOTES_DIR", tmp_path)
        with patch("friday.knowledge.adapter.ensure_vector"), \
             patch("friday.knowledge.adapter.vector.upsert"):
            note = add_note("待删除", "内容")
        with patch("friday.knowledge.adapter.vector.delete"):
            result = delete_note(note.id)
        assert result
        assert not (tmp_path / f"{note.id}.md").exists()

    def test_rejects_invalid_note_id(self) -> None:
        with pytest.raises(ValueError, match="无效的 note_id"):
            delete_note("../../etc/passwd")


class TestSearch:
    def test_fts_only(self) -> None:
        with patch("friday.knowledge.adapter.get_fts") as mock_fts:
            mock_fts.return_value = MagicMock()
            with patch("friday.knowledge.adapter.fts_search") as mock_search:
                mock_search.return_value = [
                    SearchResult(note_id="n1", title="T", snippet="S", score=0.9, source="fts")
                ]
                results = search("测试", mode="fts")
        assert len(results) == 1
        assert results[0].source == "fts"


class TestRagQuery:
    def test_returns_answer(self) -> None:
        mock_results = [SearchResult(note_id="n1", title="T", snippet="S", score=0.9)]
        with patch("friday.knowledge.adapter.search", return_value=mock_results), \
             patch("friday.knowledge.adapter._ask_llm", return_value="这是回答"):
            answer = rag_query("测试问题")
        assert answer == "这是回答"

    def test_no_results(self) -> None:
        with patch("friday.knowledge.adapter.search", return_value=[]):
            answer = rag_query("不存在的内容")
        assert answer == "未找到相关知识。"

    def test_build_context_uses_xml_tags(self) -> None:
        results = [
            SearchResult(note_id="n1", title="标题", snippet="内容片段"),
        ]
        context = _build_context(results)
        assert "<knowledge-1>" in context
        assert "</knowledge-1>" in context


class TestDeduplicate:
    def test_keeps_highest_score(self) -> None:
        results = [
            SearchResult(note_id="a", score=0.5, source="fts"),
            SearchResult(note_id="a", score=0.9, source="vector"),
            SearchResult(note_id="b", score=0.7, source="fts"),
        ]
        deduped = _deduplicate(results)
        assert len(deduped) == 2
        assert deduped[0].note_id == "a"
        assert deduped[0].score == 0.9
        assert deduped[1].note_id == "b"

    def test_empty(self) -> None:
        assert _deduplicate([]) == []
