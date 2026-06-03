"""集成测试 — 会话管理"""

import json

import pytest

from friday.cli.session import (
    Session,
    create_session,
    save_session,
    load_session,
    list_sessions,
    SESSIONS_DIR,
)


@pytest.fixture(autouse=True)
def _cleanup_test_sessions():
    """测试后清理测试会话文件"""
    yield
    for f in SESSIONS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if "inttest_" in data.get("summary", ""):
                f.unlink()
        except Exception:
            pass


class TestSessionLifecycle:
    """会话完整生命周期"""

    def test_create_session(self) -> None:
        """创建会话包含 id 和时间戳"""
        s = create_session()
        assert s.id
        assert len(s.id) == 8
        assert s.created_at

    def test_add_messages(self) -> None:
        """添加消息后消息列表增长"""
        s = create_session()
        s.add_message("user", "inttest_你好")
        s.add_message("assistant", "你好！")
        assert len(s.messages) == 2
        assert s.summary == "inttest_你好"

    def test_save_and_load(self) -> None:
        """保存后能正确加载"""
        s = create_session()
        s.add_message("user", "inttest_保存测试")
        s.add_message("assistant", "已收到")
        path = save_session(s)

        assert path.exists()
        loaded = load_session(s.id)
        assert loaded.id == s.id
        assert len(loaded.messages) == 2
        assert loaded.messages[0].content == "inttest_保存测试"

    def test_load_nonexistent(self) -> None:
        """加载不存在的会话抛 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            load_session("nonexistent_id")

    def test_list_sessions(self) -> None:
        """列出会话包含已保存的会话"""
        s = create_session()
        s.add_message("user", "inttest_列表测试")
        save_session(s)

        sessions = list_sessions()
        ids = [sess["id"] for sess in sessions]
        assert s.id in ids

    def test_to_messages_format(self) -> None:
        """to_messages 返回 LLM 兼容格式"""
        s = create_session()
        s.add_message("user", "你好")
        s.add_message("assistant", "你好！")
        msgs = s.to_messages()
        assert len(msgs) == 2
        for m in msgs:
            assert "role" in m
            assert "content" in m
            assert m["role"] in ("user", "assistant")

    def test_session_json_structure(self) -> None:
        """保存的 JSON 文件结构完整"""
        s = create_session()
        s.add_message("user", "inttest_JSON测试")
        path = save_session(s)
        data = json.loads(path.read_text(encoding="utf-8"))

        assert "id" in data
        assert "created_at" in data
        assert "summary" in data
        assert "messages" in data
        assert len(data["messages"]) == 1
        assert data["messages"][0]["role"] == "user"
