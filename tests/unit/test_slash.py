"""slash.py 单元测试 — 斜杠命令分发"""

from friday.cli.session import Session
from friday.cli.slash import CommandResult, dispatch


class TestDispatch:
    def test_non_slash_returns_none(self) -> None:
        s = Session(id="t", created_at="")
        assert dispatch("你好", s) is None

    def test_unknown_command(self) -> None:
        s = Session(id="t", created_at="")
        result = dispatch("/unknown", s)
        assert result is not None
        assert not result.should_exit

    def test_exit_command(self) -> None:
        s = Session(id="t", created_at="")
        result = dispatch("/exit", s)
        assert result.should_exit

    def test_quit_command(self) -> None:
        s = Session(id="t", created_at="")
        result = dispatch("/quit", s)
        assert result.should_exit

    def test_help_command(self) -> None:
        s = Session(id="t", created_at="")
        result = dispatch("/help", s)
        assert not result.should_exit

    def test_case_insensitive(self) -> None:
        s = Session(id="t", created_at="")
        result = dispatch("/HELP", s)
        assert not result.should_exit

    def test_load_without_args(self) -> None:
        s = Session(id="t", created_at="")
        result = dispatch("/load", s)
        assert not result.should_exit

    def test_load_invalid_number(self) -> None:
        s = Session(id="t", created_at="")
        result = dispatch("/load abc", s)
        assert not result.should_exit

    def test_load_out_of_range(self) -> None:
        s = Session(id="t", created_at="")
        result = dispatch("/load 999", s)
        assert not result.should_exit


class TestCommandResult:
    def test_defaults(self) -> None:
        r = CommandResult()
        assert not r.should_exit
        assert r.message == ""

    def test_exit_result(self) -> None:
        r = CommandResult(should_exit=True)
        assert r.should_exit
