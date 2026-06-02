"""输出处理测试"""

from friday.executor.output import format_output, format_error


class TestFormatOutput:
    """format_output() 截断逻辑"""

    def test_short_output_unchanged(self) -> None:
        assert format_output("hello") == "hello"

    def test_exactly_20_lines_unchanged(self) -> None:
        text = "\n".join([f"line {i}" for i in range(20)]) + "\n"
        assert format_output(text) == text

    def test_21_lines_truncated(self) -> None:
        text = "\n".join([f"line {i}" for i in range(21)]) + "\n"
        result = format_output(text)
        assert "输出已截断" in result
        assert "共 21 行" in result

    def test_empty_output(self) -> None:
        assert format_output("") == ""


class TestFormatError:
    """format_error() 友好错误消息"""

    def test_command_not_found(self) -> None:
        assert "命令未找到" in format_error(127, "")

    def test_permission_denied(self) -> None:
        assert "权限不足" in format_error(126, "")

    def test_unknown_error_with_stderr(self) -> None:
        result = format_error(1, "something failed")
        assert "something failed" in result

    def test_unknown_error_no_stderr(self) -> None:
        result = format_error(1, "")
        assert "退出码: 1" in result

    def test_none_exit_code(self) -> None:
        result = format_error(None, "timeout")
        assert "timeout" in result
