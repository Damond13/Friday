"""命令执行引擎测试"""

import asyncio

import pytest

from friday.executor.runner import run, ExecutionResult
from friday.executor.errors import CommandTimeoutError


class TestRun:
    """run() 异步命令执行"""

    @pytest.mark.asyncio
    async def test_echo_hello(self) -> None:
        result = await run("echo hello")
        assert result.exit_code == 0
        assert "hello" in result.stdout
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_command_not_found(self) -> None:
        result = await run("nonexistent_cmd_xyz_12345")
        assert result.exit_code == 127

    @pytest.mark.asyncio
    async def test_timeout_raises(self) -> None:
        with pytest.raises(CommandTimeoutError):
            await run("sleep 60", timeout=0.5)

    @pytest.mark.asyncio
    async def test_stderr_captured(self) -> None:
        result = await run("echo error >&2")
        assert result.exit_code == 0
        assert "error" in result.stderr

    @pytest.mark.asyncio
    async def test_nonzero_exit_code(self) -> None:
        result = await run("exit 42")
        assert result.exit_code == 42

    @pytest.mark.asyncio
    async def test_result_fields(self) -> None:
        result = await run("echo test")
        assert isinstance(result, ExecutionResult)
        assert result.command == "echo test"
        assert result.truncated is False
