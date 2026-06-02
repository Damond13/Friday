"""命令执行引擎 — asyncio subprocess 封装"""

import asyncio
import os
import time
from dataclasses import dataclass
from typing import AsyncIterator

from friday.executor.errors import CommandTimeoutError
from friday.executor.safety import SafetyLevel

DEFAULT_TIMEOUT = 30.0
MAX_OUTPUT_BYTES = 4096


@dataclass
class ExecutionResult:
    """命令执行结果"""
    command: str
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    safety_level: SafetyLevel = SafetyLevel.CONFIRM
    approved: bool = False
    truncated: bool = False


@dataclass
class StreamChunk:
    """流式输出块"""
    type: str  # "stdout" | "stderr" | "done"
    data: str = ""


async def run(
    command: str,
    cwd: str | None = None,
    timeout: float | None = None,
) -> ExecutionResult:
    """执行命令并返回结果"""
    started_at = time.monotonic()
    result = ExecutionResult(command=command)
    try:
        proc = await _create_process(command, cwd)
        stdout_bytes, stderr_bytes = await _communicate(proc, timeout)
        _fill_output(result, proc, stdout_bytes, stderr_bytes)
    except asyncio.TimeoutError:
        _kill_process(proc)
        raise CommandTimeoutError(f"命令超时 ({timeout or DEFAULT_TIMEOUT}s): {command}")
    except asyncio.CancelledError:
        _kill_process(proc)
        raise
    finally:
        result.duration_ms = int((time.monotonic() - started_at) * 1000)
    return result


async def run_stream(
    command: str,
    cwd: str | None = None,
    timeout: float | None = None,
) -> AsyncIterator[StreamChunk]:
    """流式执行命令，逐步产出输出"""
    proc = await _create_process(command, cwd)
    try:
        async with asyncio.timeout(timeout or DEFAULT_TIMEOUT):
            async for chunk in _read_lines(proc.stdout, "stdout"):
                yield chunk
            async for chunk in _read_lines(proc.stderr, "stderr"):
                yield chunk
        await proc.wait()
        yield StreamChunk(type="done", data=str(proc.returncode))
    except asyncio.TimeoutError:
        _kill_process(proc)
        raise CommandTimeoutError(f"命令超时 ({timeout or DEFAULT_TIMEOUT}s): {command}")
    except asyncio.CancelledError:
        _kill_process(proc)
        raise


async def _create_process(command: str, cwd: str | None) -> asyncio.subprocess.Process:
    """创建子进程"""
    return await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )


async def _communicate(
    proc: asyncio.subprocess.Process, timeout: float | None,
) -> tuple[bytes, bytes]:
    """与子进程通信，带超时"""
    return await asyncio.wait_for(
        proc.communicate(), timeout=timeout or DEFAULT_TIMEOUT,
    )


def _fill_output(
    result: ExecutionResult,
    proc: asyncio.subprocess.Process,
    stdout_bytes: bytes,
    stderr_bytes: bytes,
) -> None:
    """填充执行结果的输出字段"""
    result.exit_code = proc.returncode
    result.stdout = _truncate(stdout_bytes.decode("utf-8", errors="replace"))
    result.stderr = _truncate(stderr_bytes.decode("utf-8", errors="replace"))
    result.truncated = (
        len(stdout_bytes) > MAX_OUTPUT_BYTES
        or len(stderr_bytes) > MAX_OUTPUT_BYTES
    )


async def _read_lines(
    stream: asyncio.StreamReader, chunk_type: str,
) -> AsyncIterator[StreamChunk]:
    """逐行读取流输出"""
    while True:
        line = await stream.readline()
        if not line:
            break
        yield StreamChunk(type=chunk_type, data=line.decode("utf-8", errors="replace"))


def _truncate(text: str) -> str:
    """截断文本到最大字节数"""
    encoded = text.encode("utf-8")
    if len(encoded) <= MAX_OUTPUT_BYTES:
        return text
    return encoded[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")


def _kill_process(proc: asyncio.subprocess.Process | None) -> None:
    """优雅终止子进程"""
    if proc is None or proc.returncode is not None:
        return
    try:
        proc.terminate()
    except ProcessLookupError:
        return
    try:
        os.waitpid(proc.pid, 0)
    except (ChildProcessError, OSError):
        pass
