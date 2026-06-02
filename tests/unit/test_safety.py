"""安全策略分类测试"""

import tempfile
from pathlib import Path

import pytest

from friday.executor.safety import SafetyLevel, classify, add_trusted, _extract_command_name


class TestClassify:
    """classify() 安全分类"""

    def test_safe_commands(self) -> None:
        for cmd in ["ls", "ls -la", "pwd", "cat file.txt", "echo hello", "git status"]:
            assert classify(cmd) == SafetyLevel.SAFE, f"{cmd} should be SAFE"

    def test_dangerous_rm_rf(self) -> None:
        assert classify("rm -rf /tmp/test") == SafetyLevel.DANGEROUS

    def test_dangerous_sudo(self) -> None:
        assert classify("sudo apt install foo") == SafetyLevel.DANGEROUS

    def test_dangerous_mkfs(self) -> None:
        assert classify("mkfs.ext4 /dev/sda1") == SafetyLevel.DANGEROUS

    def test_dangerous_shutdown(self) -> None:
        assert classify("shutdown -h now") == SafetyLevel.DANGEROUS

    def test_confirm_unknown(self) -> None:
        assert classify("pip install requests") == SafetyLevel.CONFIRM
        assert classify("docker build .") == SafetyLevel.CONFIRM

    def test_dangerous_priority_over_safe(self) -> None:
        assert classify("sudo ls") == SafetyLevel.DANGEROUS

    def test_empty_command(self) -> None:
        assert classify("") == SafetyLevel.CONFIRM


class TestTrusted:
    """信任命令管理"""

    def test_add_trusted_upgrades_to_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            assert classify("docker ps", db_path=db) == SafetyLevel.CONFIRM
            add_trusted("docker", db_path=db)
            assert classify("docker ps", db_path=db) == SafetyLevel.SAFE


class TestExtractCommandName:
    """命令名提取"""

    def test_simple(self) -> None:
        assert _extract_command_name("ls -la") == "ls"

    def test_with_path(self) -> None:
        assert _extract_command_name("/usr/bin/git status") == "/usr/bin/git"

    def test_empty(self) -> None:
        assert _extract_command_name("") == ""
