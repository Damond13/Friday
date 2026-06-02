"""执行历史记录测试"""

import tempfile
from pathlib import Path

from friday.executor.history import init_db, save_record, get_history, clean_old_records
from friday.executor.runner import ExecutionResult
from friday.executor.safety import SafetyLevel


def _make_result(command: str = "echo test", exit_code: int = 0) -> ExecutionResult:
    return ExecutionResult(
        command=command, exit_code=exit_code, stdout="ok",
        duration_ms=10, safety_level=SafetyLevel.SAFE,
    )


class TestHistory:
    """历史记录存取"""

    def test_save_and_get(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            init_db(db)
            save_record(_make_result("echo a"), cwd="/tmp", db_path=db)
            save_record(_make_result("echo b"), cwd="/tmp", db_path=db)
            records = get_history(limit=10, db_path=db)
            assert len(records) == 2
            assert records[0].command == "echo b"

    def test_empty_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            init_db(db)
            assert get_history(db_path=db) == []

    def test_record_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            init_db(db)
            save_record(_make_result("ls -la", 0), cwd="/home", db_path=db)
            rec = get_history(db_path=db)[0]
            assert rec.command == "ls -la"
            assert rec.cwd == "/home"
            assert rec.exit_code == 0
            assert rec.safety_level == "safe"

    def test_clean_old_records_no_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            init_db(db)
            save_record(_make_result(), db_path=db)
            count = clean_old_records(db)
            assert count >= 0

    def test_db_creates_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "sub" / "dir" / "test.db"
            init_db(db)
            assert db.exists()
