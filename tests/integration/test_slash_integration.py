"""集成测试 — 斜杠命令"""

from unittest.mock import patch

import pytest

from friday.cli.slash import CommandResult, dispatch, get_commands
from friday.cli.session import Session


@pytest.fixture(autouse=True)
def _skip_vector_indexing():
    """跳过向量索引，避免 embedding 模型下载"""
    with patch("friday.knowledge.vector.upsert"), \
         patch("friday.knowledge.vector.delete"), \
         patch("friday.knowledge.vector.search", return_value=[]), \
         patch("friday.knowledge.vector.init_vector"):
        yield


@pytest.fixture
def session() -> Session:
    """创建测试会话"""
    return Session(id="inttest", created_at="2026-06-03T00:00:00")


class TestSlashDispatch:
    """斜杠命令分发"""

    def test_non_slash_returns_none(self, session: Session) -> None:
        """非斜杠输入返回 None"""
        result = dispatch("你好", session)
        assert result is None

    def test_unknown_command(self, session: Session) -> None:
        """未知命令返回 CommandResult"""
        result = dispatch("/unknown_cmd_xyz", session)
        assert isinstance(result, CommandResult)
        assert result.should_exit is False

    def test_exit_command(self, session: Session) -> None:
        """/exit 返回 should_exit"""
        result = dispatch("/exit", session)
        assert result.should_exit is True

    def test_quit_command(self, session: Session) -> None:
        """/quit 等效 /exit"""
        result = dispatch("/quit", session)
        assert result.should_exit is True

    def test_case_insensitive(self, session: Session) -> None:
        """命令不区分大小写"""
        result = dispatch("/EXIT", session)
        assert result.should_exit is True

    def test_help_command(self, session: Session) -> None:
        """/help 返回正常结果"""
        result = dispatch("/help", session)
        assert isinstance(result, CommandResult)
        assert result.should_exit is False


class TestRegisteredCommands:
    """已注册命令完整性"""

    def test_all_commands_registered(self) -> None:
        """核心命令全部注册"""
        cmds = get_commands()
        expected = {"help", "exit", "quit", "save", "history", "load", "note", "search"}
        assert expected == set(cmds.keys())

    def test_command_has_description(self) -> None:
        """每个命令有描述"""
        cmds = get_commands()
        for name, (desc, handler) in cmds.items():
            assert desc, f"命令 /{name} 缺少描述"


class TestSlashNoteSearch:
    """笔记和搜索命令"""

    def test_note_without_args(self, session: Session) -> None:
        """/note 无参数提示用法"""
        result = dispatch("/note", session)
        assert isinstance(result, CommandResult)

    def test_note_with_content(self, session: Session) -> None:
        """/note 带内容创建笔记"""
        from friday.knowledge.adapter import delete_note
        result = dispatch("/note inttest_斜杠笔记测试内容", session)
        assert isinstance(result, CommandResult)
        # 清理
        notes = __import__("friday.knowledge.adapter", fromlist=["list_notes"]).list_notes()
        for n in notes:
            if "inttest_斜杠笔记" in n.title:
                delete_note(n.id)

    def test_search_without_args(self, session: Session) -> None:
        """/search 无参数提示用法"""
        result = dispatch("/search", session)
        assert isinstance(result, CommandResult)

    def test_search_with_query(self, session: Session) -> None:
        """/search 带查询词搜索"""
        result = dispatch("/search inttest_nonexistent", session)
        assert isinstance(result, CommandResult)
