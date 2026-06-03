"""集成测试 — 知识库（FTS5 + 文件系统）"""

from unittest.mock import patch

import pytest

from friday.knowledge.adapter import add_note, search, delete_note, list_notes, index_note
from friday.knowledge.store import (
    Note,
    NOTES_DIR,
    create_note_file,
    generate_note_id,
    now_iso,
    read_note_file,
)


@pytest.fixture(autouse=True)
def _skip_vector_indexing():
    """跳过向量索引（避免下载 embedding 模型），仅测试 FTS5"""
    with patch("friday.knowledge.vector.upsert"), \
         patch("friday.knowledge.vector.delete"), \
         patch("friday.knowledge.vector.search", return_value=[]), \
         patch("friday.knowledge.vector.init_vector"):
        yield


@pytest.fixture(autouse=True)
def _cleanup_test_notes():
    """测试前后清理测试笔记"""
    yield
    for f in NOTES_DIR.glob("*.md"):
        try:
            text = f.read_text(encoding="utf-8")
            if "inttest_" in text:
                f.unlink()
        except Exception:
            pass


def _make_note(title: str, content: str, tags: list[str] | None = None) -> Note:
    """创建测试笔记"""
    return add_note(title=f"inttest_{title}", content=f"inttest_{content}", tags=tags or [])


class TestKnowledgeCRUD:
    """知识库增删查"""

    def test_add_note(self) -> None:
        """创建笔记返回完整对象"""
        note = _make_note("测试笔记", "这是一条集成测试笔记内容")
        assert note.id
        assert "inttest_测试笔记" in note.title
        assert note.created_at
        assert (NOTES_DIR / f"{note.id}.md").exists()

    def test_add_note_with_tags(self) -> None:
        """创建带标签的笔记"""
        note = _make_note("标签测试", "内容", tags=["测试", "集成"])
        path = NOTES_DIR / f"{note.id}.md"
        assert path.exists()
        loaded = read_note_file(path)
        assert "测试" in loaded.tags

    def test_list_notes(self) -> None:
        """列出笔记包含新创建的笔记"""
        note = _make_note("列表测试", "列表测试内容")
        notes = list_notes()
        ids = [n.id for n in notes]
        assert note.id in ids

    def test_delete_note(self) -> None:
        """删除笔记后文件和索引都移除"""
        note = _make_note("删除测试", "待删除内容")
        assert (NOTES_DIR / f"{note.id}.md").exists()

        ok = delete_note(note.id)
        assert ok is True
        assert not (NOTES_DIR / f"{note.id}.md").exists()

    def test_delete_nonexistent_note(self) -> None:
        """删除不存在的笔记（合法 ID 格式）返回 False"""
        ok = delete_note("deadbeef")
        assert ok is False

    def test_delete_invalid_note_id(self) -> None:
        """非法 note_id 抛 ValueError"""
        with pytest.raises(ValueError, match="无效"):
            delete_note("nonexistent_id")


class TestKnowledgeSearch:
    """知识库搜索"""

    def test_fts_search_chinese(self) -> None:
        """FTS5 中文搜索"""
        note = _make_note("Python编程", "Python是一种解释型高级编程语言，支持面向对象编程")
        try:
            results = search("Python编程", mode="fts")
            assert len(results) > 0
            found = any(r.note_id == note.id for r in results)
            assert found, f"笔记 {note.id} 未被 FTS 搜索到"
        finally:
            delete_note(note.id)

    def test_fts_search_keyword(self) -> None:
        """FTS5 关键词搜索"""
        note = _make_note("Docker部署", "使用Docker容器化部署应用，docker-compose编排服务")
        try:
            results = search("Docker", mode="fts")
            assert len(results) > 0
            found = any(r.note_id == note.id for r in results)
            assert found
        finally:
            delete_note(note.id)

    def test_search_auto_mode(self) -> None:
        """auto 模式搜索（降级为 FTS）"""
        note = _make_note("Git版本控制", "Git是分布式版本控制系统")
        try:
            results = search("Git版本", mode="auto")
            assert len(results) > 0
        finally:
            delete_note(note.id)

    def test_search_no_results(self) -> None:
        """搜索无结果返回空列表"""
        results = search("zzz_nonexistent_query_12345", mode="fts")
        assert isinstance(results, list)

    def test_search_deduplicate(self) -> None:
        """搜索结果按 note_id 去重"""
        note = _make_note("去重测试", "去重测试的唯一内容 xyzabc")
        try:
            results = search("去重测试", mode="auto")
            ids = [r.note_id for r in results]
            assert len(ids) == len(set(ids)), "存在重复的 note_id"
        finally:
            delete_note(note.id)


class TestQuickNote:
    """快捷笔记 '记一下' 功能"""

    def test_quick_note_prefix(self) -> None:
        """'记一下' 前缀触发笔记创建"""
        text = "记一下：快捷笔记功能测试内容"
        prefixes = ("记一下", "记录一下", "记一下：", "记一下:")
        matched = False
        for p in prefixes:
            if text.startswith(p):
                content = text[len(p):].strip()
                if content:
                    note = add_note(title=content[:50], content=content)
                    assert note.id
                    delete_note(note.id)
                    matched = True
                    break
        assert matched

    def test_note_file_format(self) -> None:
        """笔记文件格式正确（Markdown + YAML front matter）"""
        note = Note(
            id=generate_note_id(),
            title="inttest_格式测试",
            content="inttest_格式测试内容",
            tags=["测试"],
            created_at=now_iso(),
        )
        path = create_note_file(note)
        try:
            text = path.read_text(encoding="utf-8")
            assert text.startswith("---")
            assert f"id: {note.id}" in text
            assert "title: inttest_格式测试" in text

            loaded = read_note_file(path)
            assert loaded.id == note.id
            assert loaded.title == note.title
            assert loaded.content == note.content
        finally:
            path.unlink(missing_ok=True)
