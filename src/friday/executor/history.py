"""执行历史记录 — SQLite 存储"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from friday.executor.runner import ExecutionResult
from friday.executor.safety import DB_PATH

RETENTION_DAYS = 90


@dataclass
class ExecutionRecord:
    """执行历史记录"""
    id: int = 0
    command: str = ""
    cwd: str = ""
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_ms: int = 0
    safety_level: str = ""
    approved: bool = False


def init_db(db_path: Path = DB_PATH) -> None:
    """初始化数据库和表"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                cwd TEXT NOT NULL,
                exit_code INTEGER,
                stdout TEXT DEFAULT '',
                stderr TEXT DEFAULT '',
                started_at TEXT NOT NULL,
                finished_at TEXT,
                duration_ms INTEGER,
                safety_level TEXT NOT NULL CHECK(safety_level IN ('safe', 'confirm', 'dangerous')),
                approved INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_exec_started_at ON execution_log(started_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_exec_command ON execution_log(command)")
        conn.commit()
    finally:
        conn.close()
    clean_old_records(db_path)


def save_record(result: ExecutionResult, cwd: str | None = None, db_path: Path = DB_PATH) -> int:
    """保存执行记录，返回记录 ID"""
    init_db(db_path)
    now = datetime.now().isoformat(timespec="seconds")
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute("""
            INSERT INTO execution_log (command, cwd, exit_code, stdout, stderr, started_at, finished_at, duration_ms, safety_level, approved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.command,
            cwd or ".",
            result.exit_code,
            result.stdout[:4096],
            result.stderr[:4096],
            now,
            now,
            result.duration_ms,
            result.safety_level.value,
            1 if result.approved else 0,
        ))
        conn.commit()
        return cursor.lastrowid or 0
    finally:
        conn.close()


def get_history(limit: int = 20, offset: int = 0, db_path: Path = DB_PATH) -> list[ExecutionRecord]:
    """查询最近的执行历史"""
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT id, command, cwd, exit_code, started_at, finished_at, duration_ms, safety_level, approved FROM execution_log ORDER BY started_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [_row_to_record(r) for r in rows]
    finally:
        conn.close()


def clean_old_records(db_path: Path = DB_PATH) -> int:
    """清理超过保留期的记录"""
    if not db_path.exists():
        return 0
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            "DELETE FROM execution_log WHERE started_at < datetime('now', '-' || ? || ' days')",
            (RETENTION_DAYS,),
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()


def _row_to_record(row: tuple) -> ExecutionRecord:
    """将数据库行转换为 ExecutionRecord"""
    return ExecutionRecord(
        id=row[0],
        command=row[1],
        cwd=row[2],
        exit_code=row[3],
        started_at=row[4],
        finished_at=row[5],
        duration_ms=row[6] or 0,
        safety_level=row[7],
        approved=bool(row[8]),
    )
