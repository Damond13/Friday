"""集成测试 — CLI 入口（端到端）"""

import subprocess
import sys

import pytest

from tests.integration.conftest import requires_llm


def _run_friday(*args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    """运行 friday CLI 命令"""
    cmd = [sys.executable, "-m", "friday.cli.app", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=_project_root(),
    )


def _project_root() -> str:
    """获取项目根目录"""
    from pathlib import Path
    return str(Path(__file__).resolve().parent.parent.parent)


@requires_llm
class TestCLISingleShot:
    """CLI 单次执行模式"""

    def test_single_shot_returns_response(self) -> None:
        """单次提问返回非空输出"""
        result = _run_friday("说'集成测试通过'四个字")
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "集成测试通过" in result.stdout

    def test_single_shot_empty_args(self) -> None:
        """无参数时不报错（进入交互模式的边界情况）"""
        # 无参数会进入交互模式，subprocess 会因为 stdin 不是 tty 而退出
        # 但不应该 crash
        result = subprocess.run(
            [sys.executable, "-m", "friday.cli.app"],
            capture_output=True,
            text=True,
            timeout=5,
            input="",  # stdin EOF
            cwd=_project_root(),
        )
        # 应该正常退出，不应该有未捕获的异常
        assert "Traceback" not in result.stderr


class TestCLIModuleImport:
    """CLI 模块导入"""

    def test_import_app(self) -> None:
        """friday.cli.app 可导入"""
        from friday.cli.app import app, entry, main, run_single, run_interactive
        assert app is not None
        assert callable(entry)

    def test_import_repl(self) -> None:
        """friday.cli.repl 可导入"""
        from friday.cli.repl import run_repl, _process_input, _try_quick_note, _stream_reply
        assert callable(run_repl)

    def test_import_slash(self) -> None:
        """friday.cli.slash 可导入"""
        from friday.cli.slash import dispatch, get_commands, CommandResult
        assert callable(dispatch)

    def test_import_display(self) -> None:
        """friday.cli.display 可导入"""
        from friday.cli.display import (
            console, show_welcome, show_error, show_config_guide,
            show_save_success, show_history_list, show_search_results,
            show_streaming_token, show_assistant_separator,
        )
        assert console is not None
