"""安全策略管理 — 三级命令分类 + 黑白名单 + 信任管理"""

import re
import sqlite3
from enum import Enum
from pathlib import Path

from friday.config import CONFIG_DIR

DB_PATH = CONFIG_DIR / "executor.db"

SAFE_COMMANDS: frozenset[str] = frozenset({
    "ls", "pwd", "cat", "head", "tail", "echo", "wc", "find", "grep",
    "which", "date", "whoami", "uname", "git", "diff", "tree", "file", "stat",
})

DANGEROUS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\brm\s+(-[rf]+\s)", re.IGNORECASE),
    re.compile(r"\brmdir\b"),
    re.compile(r"\bsudo\b"),
    re.compile(r"\bchmod\b"),
    re.compile(r"\bchown\b"),
    re.compile(r"\bmkfs\b"),
    re.compile(r"\bdd\s+if=", re.IGNORECASE),
    re.compile(r">\s*/dev/sd"),
    re.compile(r"\bshutdown\b"),
    re.compile(r"\breboot\b"),
    re.compile(r"\bsystemctl\s+(stop|disable|mask)\b", re.IGNORECASE),
    re.compile(r"\bpip\s+install.*--force", re.IGNORECASE),
    re.compile(r"\bnpm\s+publish\b", re.IGNORECASE),
]


class SafetyLevel(Enum):
    """命令安全等级"""
    SAFE = "safe"
    CONFIRM = "confirm"
    DANGEROUS = "dangerous"


def classify(command: str, db_path: Path = DB_PATH) -> SafetyLevel:
    """对命令进行安全分类

    优先级: dangerous > trusted > safe > confirm
    """
    cmd_name = _extract_command_name(command)

    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            return SafetyLevel.DANGEROUS

    if _is_trusted(cmd_name, db_path):
        return SafetyLevel.SAFE

    if cmd_name in SAFE_COMMANDS:
        return SafetyLevel.SAFE

    return SafetyLevel.CONFIRM


def add_trusted(command_pattern: str, db_path: Path = DB_PATH) -> None:
    """将命令标记为信任"""
    _ensure_db(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT OR REPLACE INTO trusted_commands (command_pattern, trusted_at) VALUES (?, datetime('now'))",
            (command_pattern,),
        )
        conn.commit()
    finally:
        conn.close()


def _is_trusted(cmd_name: str, db_path: Path) -> bool:
    """查询信任表"""
    if not db_path.exists():
        return False
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='trusted_commands'",
        ).fetchone()
        if not row:
            return False
        row = conn.execute(
            "SELECT 1 FROM trusted_commands WHERE command_pattern = ?",
            (cmd_name,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def _extract_command_name(command: str) -> str:
    """提取命令名（第一个 token）"""
    stripped = command.strip()
    if not stripped:
        return ""
    return stripped.split()[0]


def _ensure_db(db_path: Path) -> None:
    """确保数据库和表存在"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trusted_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_pattern TEXT NOT NULL UNIQUE,
                trusted_at TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()
