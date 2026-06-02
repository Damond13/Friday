"""fts.py 单元测试 — FTS5 全文索引"""

import sqlite3
from pathlib import Path

import pytest

from friday.knowledge.fts import init_fts, insert, delete, search
import friday.knowledge.fts as fts_mod


@pytest.fixture
def fts_conn(tmp_path: Path) -> sqlite3.Connection:
    db = tmp_path / "test_fts.db"
    return init_fts(db)


class TestFTS:
    def test_insert_and_search(self, fts_conn: sqlite3.Connection) -> None:
        insert(fts_conn, "n1", "Python 装饰器", "装饰器是函数包装器", file_path="/tmp/n1.md")
        results = search(fts_conn, "装饰器")
        assert len(results) >= 1
        assert results[0].note_id == "n1"
        assert results[0].source == "fts"

    def test_chinese_search(self, fts_conn: sqlite3.Connection) -> None:
        insert(fts_conn, "n2", "部署流程", "先停 nginx 再拉代码")
        results = search(fts_conn, "代码")
        assert len(results) >= 1

    def test_delete(self, fts_conn: sqlite3.Connection) -> None:
        insert(fts_conn, "n3", "测试", "内容")
        delete(fts_conn, "n3")
        results = search(fts_conn, "内容")
        assert all(r.note_id != "n3" for r in results)

    def test_empty_query(self, fts_conn: sqlite3.Connection) -> None:
        insert(fts_conn, "n4", "标题", "内容")
        results = search(fts_conn, "")
        assert results == []

    def test_update(self, fts_conn: sqlite3.Connection) -> None:
        insert(fts_conn, "n5", "旧标题", "旧内容")
        insert(fts_conn, "n5", "新标题", "新内容")
        results = search(fts_conn, "新内容")
        assert len(results) >= 1
        assert results[0].note_id == "n5"

    def test_with_tags(self, fts_conn: sqlite3.Connection) -> None:
        insert(fts_conn, "n6", "标签测试", "内容", tags=["python", "ai"])
        results = search(fts_conn, "python")
        assert len(results) >= 1
