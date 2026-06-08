"""vector.py 单元测试 — ChromaDB 向量索引（mock embedding）"""

from pathlib import Path
from unittest.mock import patch

import pytest

from friday.knowledge.vector import init_vector, upsert, delete, search, reset_client
import friday.knowledge.vector as vector_mod

_DIM = 1024


def _fake_embedding(text: str) -> list[float]:
    """确定性伪向量，基于文本首字符生成"""
    return [float(ord(c) % 256) / 256.0 for c in text.ljust(_DIM, "\0")[:_DIM]]


@pytest.fixture(autouse=True)
def _reset():
    reset_client()
    yield
    reset_client()


@pytest.fixture
def chroma_dir(tmp_path: Path) -> Path:
    d = tmp_path / "chroma"
    d.mkdir()
    return d


@pytest.fixture(autouse=True)
def _mock_embedding():
    with patch("friday.knowledge.embedding.embed_text", side_effect=_fake_embedding):
        yield


class TestVector:
    def test_upsert_and_search(self, chroma_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(vector_mod, "_CHROMA_DIR", chroma_dir)
        init_vector(chroma_dir)
        upsert("v1", "Python 装饰器就是函数包装器", title="装饰器", file_path="/tmp/v1.md")
        results = search("Python 装饰器就是函数包装器", limit=3)
        assert len(results) >= 1
        assert results[0].note_id == "v1"

    def test_delete(self, chroma_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(vector_mod, "_CHROMA_DIR", chroma_dir)
        init_vector(chroma_dir)
        upsert("v2", "待删除的内容", title="删除测试")
        delete("v2")
        results = search("待删除的内容")
        assert all(r.note_id != "v2" for r in results)

    def test_search_empty(self, chroma_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(vector_mod, "_CHROMA_DIR", chroma_dir)
        init_vector(chroma_dir)
        results = search("不存在的内容")
        assert results == []


class TestEntryType:
    def test_upsert_default_type_is_note(self, chroma_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(vector_mod, "_CHROMA_DIR", chroma_dir)
        init_vector(chroma_dir)
        upsert("vt1", "默认类型内容", title="测试")
        results = search("默认类型内容", entry_type="note")
        assert any(r.note_id == "vt1" for r in results)

    def test_upsert_instruction_type(self, chroma_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(vector_mod, "_CHROMA_DIR", chroma_dir)
        init_vector(chroma_dir)
        upsert("vt2", "部署指令内容", title="部署", entry_type="instruction")
        instr_results = search("部署指令内容", entry_type="instruction")
        note_results = search("部署指令内容", entry_type="note")
        assert any(r.note_id == "vt2" for r in instr_results)
        assert not any(r.note_id == "vt2" for r in note_results)

    def test_search_no_filter_returns_all(self, chroma_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(vector_mod, "_CHROMA_DIR", chroma_dir)
        init_vector(chroma_dir)
        upsert("vt3", "笔记内容", entry_type="note")
        upsert("vt4", "指令内容", entry_type="instruction")
        results = search("内容")
        ids = {r.note_id for r in results}
        assert "vt3" in ids or "vt4" in ids
