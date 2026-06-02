"""session.py 单元测试 — 会话存储"""

import json
from pathlib import Path

from friday.cli.session import (
    Message,
    Session,
    create_session,
    load_session,
    list_sessions,
    save_session,
)


class TestMessage:
    def test_to_dict(self) -> None:
        m = Message(role="user", content="hello")
        assert m.to_dict() == {"role": "user", "content": "hello"}

    def test_from_dict(self) -> None:
        m = Message.from_dict({"role": "assistant", "content": "hi"})
        assert m.role == "assistant"
        assert m.content == "hi"


class TestSession:
    def test_to_dict(self) -> None:
        s = Session(id="abc", created_at="2026-01-01", summary="test")
        s.messages.append(Message(role="user", content="hello"))
        d = s.to_dict()
        assert d["id"] == "abc"
        assert len(d["messages"]) == 1

    def test_from_dict(self) -> None:
        data = {
            "id": "abc",
            "created_at": "2026-01-01",
            "summary": "test",
            "messages": [{"role": "user", "content": "hello"}],
        }
        s = Session.from_dict(data)
        assert s.id == "abc"
        assert len(s.messages) == 1
        assert s.messages[0].content == "hello"

    def test_to_messages(self) -> None:
        s = Session(id="x", created_at="")
        s.add_message("user", "hi")
        s.add_message("assistant", "hello")
        msgs = s.to_messages()
        assert msgs == [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]

    def test_add_message_updates_summary(self) -> None:
        s = Session()
        s.add_message("user", "这是一段很长的测试消息，用来验证摘要截断功能是否正常工作")
        assert s.summary == "这是一段很长的测试消息，用来验证摘要截断功能是否正常工作"[:50]

    def test_add_message_no_summary_for_assistant(self) -> None:
        s = Session()
        s.add_message("assistant", "reply")
        assert s.summary == ""


class TestSessionStorage:
    def test_create_session(self) -> None:
        s = create_session()
        assert len(s.id) == 8
        assert s.created_at != ""
        assert s.messages == []

    def test_save_and_load(self, tmp_path: Path) -> None:
        import friday.cli.session as mod
        original_dir = mod.SESSIONS_DIR
        mod.SESSIONS_DIR = tmp_path
        try:
            s = create_session()
            s.add_message("user", "hello")
            path = save_session(s)
            assert path.exists()
            loaded = load_session(s.id)
            assert loaded.id == s.id
            assert len(loaded.messages) == 1
            assert loaded.messages[0].content == "hello"
        finally:
            mod.SESSIONS_DIR = original_dir

    def test_list_sessions(self, tmp_path: Path) -> None:
        import friday.cli.session as mod
        original_dir = mod.SESSIONS_DIR
        mod.SESSIONS_DIR = tmp_path
        try:
            s1 = create_session()
            s1.add_message("user", "first")
            save_session(s1)
            s2 = create_session()
            s2.add_message("user", "second")
            save_session(s2)
            sessions = list_sessions()
            assert len(sessions) == 2
        finally:
            mod.SESSIONS_DIR = original_dir

    def test_list_sessions_empty(self, tmp_path: Path) -> None:
        import friday.cli.session as mod
        original_dir = mod.SESSIONS_DIR
        mod.SESSIONS_DIR = tmp_path
        try:
            assert list_sessions() == []
        finally:
            mod.SESSIONS_DIR = original_dir
