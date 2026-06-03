"""集成测试 — 执行器（安全策略 + 异步执行）"""

import asyncio

import pytest

from friday.executor.safety import SafetyLevel, classify, add_trusted
from friday.executor.runner import run
from friday.executor.errors import CommandTimeoutError
from friday.executor.history import init_db, save_record, get_history, DB_PATH
from friday.executor.runner import ExecutionResult


class TestSafetyClassification:
    """安全策略分类"""

    @pytest.mark.parametrize("command,expected", [
        ("ls -la", SafetyLevel.SAFE),
        ("pwd", SafetyLevel.SAFE),
        ("cat README.md", SafetyLevel.SAFE),
        ("git status", SafetyLevel.SAFE),
        ("find . -name '*.py'", SafetyLevel.SAFE),
        ("grep -r pattern .", SafetyLevel.SAFE),
        ("tree -L 2", SafetyLevel.SAFE),
        ("wc -l file.txt", SafetyLevel.SAFE),
        ("python --version", SafetyLevel.CONFIRM),
        ("docker ps", SafetyLevel.CONFIRM),
        ("rm -rf /", SafetyLevel.DANGEROUS),
        ("sudo apt install xxx", SafetyLevel.DANGEROUS),
        ("shutdown -h now", SafetyLevel.DANGEROUS),
        ("mkfs.ext4 /dev/sda1", SafetyLevel.DANGEROUS),
        ("chmod 777 /etc/passwd", SafetyLevel.DANGEROUS),
        ("dd if=/dev/zero of=/dev/sda", SafetyLevel.DANGEROUS),
    ])
    def test_classify(self, command: str, expected: SafetyLevel) -> None:
        """命令安全分类"""
        assert classify(command) == expected

    def test_dangerous_priority_over_safe(self) -> None:
        """危险模式优先于安全命令"""
        # git 是安全的，但 sudo git 不是
        assert classify("sudo git status") == SafetyLevel.DANGEROUS

    def test_empty_command(self) -> None:
        """空命令"""
        assert classify("") == SafetyLevel.CONFIRM


class TestExecutorRunner:
    """命令执行引擎"""

    def test_echo(self) -> None:
        """执行 echo 命令"""
        result = asyncio.run(run("echo hello_integration"))
        assert result.exit_code == 0
        assert "hello_integration" in result.stdout

    def test_pwd(self) -> None:
        """执行 pwd 命令"""
        result = asyncio.run(run("pwd"))
        assert result.exit_code == 0
        assert result.stdout.strip()

    def test_nonzero_exit(self) -> None:
        """非零退出码"""
        result = asyncio.run(run("ls /nonexistent_dir_inttest_12345 2>&1"))
        assert result.exit_code != 0

    def test_stderr_captured(self) -> None:
        """stderr 被捕获"""
        result = asyncio.run(run("echo error_msg >&2"))
        assert "error_msg" in result.stderr

    def test_timeout(self) -> None:
        """超时抛出 CommandTimeoutError"""
        with pytest.raises(CommandTimeoutError):
            asyncio.run(run("sleep 5", timeout=0.3))

    def test_result_has_duration(self) -> None:
        """执行结果包含耗时"""
        result = asyncio.run(run("echo timing"))
        assert result.duration_ms >= 0


class TestExecutionHistory:
    """执行历史记录"""

    def test_save_and_get(self, tmp_path) -> None:
        """保存和查询执行记录"""
        from pathlib import Path
        db = tmp_path / "test_history.db"
        init_db(db)

        result = ExecutionResult(
            command="echo test",
            exit_code=0,
            stdout="test\n",
            duration_ms=100,
            safety_level=SafetyLevel.SAFE,
        )
        record_id = save_record(result, cwd="/tmp", db_path=db)
        assert record_id > 0

        records = get_history(db_path=db)
        assert len(records) >= 1
        assert records[0].command == "echo test"

    def test_empty_history(self, tmp_path) -> None:
        """空数据库返回空列表"""
        from pathlib import Path
        db = tmp_path / "empty.db"
        records = get_history(db_path=db)
        assert records == []
