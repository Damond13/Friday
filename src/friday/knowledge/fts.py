"""FTS5 全文索引管理 — SQLite + jieba 中文分词"""

import sqlite3
from pathlib import Path

import jieba

from friday.knowledge.store import SearchResult

_DB_PATH = Path.home() / ".friday" / "knowledge" / "fts.db"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS notes_fts (
    note_id TEXT PRIMARY KEY,
    title TEXT,
    content TEXT,
    tags TEXT,
    file_path TEXT,
    mtime REAL DEFAULT 0
);
"""

_CREATE_FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts_index
USING fts5(note_id, title, content, tags, file_path, content=notes_fts, content_rowid=rowid);
"""

_TRIGGER_INSERT = """
CREATE TRIGGER IF NOT EXISTS notes_fts_ai AFTER INSERT ON notes_fts BEGIN
    INSERT INTO notes_fts_index(rowid, note_id, title, content, tags, file_path)
    VALUES (new.rowid, new.note_id, new.title, new.content, new.tags, new.file_path);
END;
"""

_TRIGGER_DELETE = """
CREATE TRIGGER IF NOT EXISTS notes_fts_ad AFTER DELETE ON notes_fts BEGIN
    INSERT INTO notes_fts_index(notes_fts_index, rowid, note_id, title, content, tags, file_path)
    VALUES ('delete', old.rowid, old.note_id, old.title, old.content, old.tags, old.file_path);
END;
"""

_TRIGGER_UPDATE = """
CREATE TRIGGER IF NOT EXISTS notes_fts_au AFTER UPDATE ON notes_fts BEGIN
    INSERT INTO notes_fts_index(notes_fts_index, rowid, note_id, title, content, tags, file_path)
    VALUES ('delete', old.rowid, old.note_id, old.title, old.content, old.tags, old.file_path);
    INSERT INTO notes_fts_index(rowid, note_id, title, content, tags, file_path)
    VALUES (new.rowid, new.note_id, new.title, new.content, new.tags, new.file_path);
END;
"""


def _get_conn(db_path: Path | None = None) -> sqlite3.Connection:
    """获取 SQLite 连接"""
    path = db_path or _DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    """初始化数据库表和触发器"""
    conn.executescript(_CREATE_TABLE_SQL)
    conn.executescript(_CREATE_FTS_SQL)
    conn.executescript(_TRIGGER_INSERT)
    conn.executescript(_TRIGGER_DELETE)
    conn.executescript(_TRIGGER_UPDATE)
    try:
        conn.execute("ALTER TABLE notes_fts ADD COLUMN mtime REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    conn.commit()


def _tokenize(text: str) -> str:
    """jieba 分词，返回空格分隔的词语"""
    return " ".join(jieba.cut_for_search(text))


def init_fts(db_path: Path | None = None) -> sqlite3.Connection:
    """初始化 FTS 索引，返回连接"""
    conn = _get_conn(db_path)
    _init_db(conn)
    return conn


def insert(conn: sqlite3.Connection, note_id: str, title: str, content: str,
           tags: list[str] | None = None, file_path: str = "",
           mtime: float = 0.0) -> None:
    """插入或更新索引条目"""
    conn.execute("DELETE FROM notes_fts WHERE note_id = ?", (note_id,))
    tokenized_title = _tokenize(title)
    tokenized_content = _tokenize(content)
    tokenized_tags = _tokenize(" ".join(tags)) if tags else ""
    conn.execute(
        "INSERT INTO notes_fts (note_id, title, content, tags, file_path, mtime) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (note_id, tokenized_title, tokenized_content, tokenized_tags, file_path, mtime),
    )
    conn.commit()


def delete(conn: sqlite3.Connection, note_id: str) -> None:
    """删除索引条目"""
    conn.execute("DELETE FROM notes_fts WHERE note_id = ?", (note_id,))
    conn.commit()


def search(conn: sqlite3.Connection, query: str, limit: int = 5) -> list[SearchResult]:
    """FTS5 全文搜索"""
    tokenized_query = _tokenize(query)
    if not tokenized_query.strip():
        return []
    fts_query = " OR ".join(tokenized_query.split())
    rows = conn.execute(
        "SELECT note_id, title, content, file_path "
        "FROM notes_fts_index WHERE notes_fts_index MATCH ? LIMIT ?",
        (fts_query, limit),
    ).fetchall()
    return [
        SearchResult(
            note_id=r[0], title=r[1],
            snippet=_extract_snippet(r[2], query),
            score=1.0, source="fts", file_path=r[3],
        )
        for r in rows
    ]


def get_all_index_mtimes(conn: sqlite3.Connection) -> dict[str, float]:
    """返回所有已索引笔记的 {note_id: mtime}"""
    rows = conn.execute("SELECT note_id, mtime FROM notes_fts").fetchall()
    return {r[0]: r[1] or 0.0 for r in rows}


def _extract_snippet(content: str, query: str, max_len: int = 100) -> str:
    """从内容中提取匹配片段"""
    lower = content.lower()
    q_lower = query.lower()
    idx = lower.find(q_lower)
    if idx == -1:
        return content[:max_len] + ("..." if len(content) > max_len else "")
    start = max(0, idx - 20)
    end = min(len(content), idx + len(query) + 80)
    snippet = content[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."
    return snippet
