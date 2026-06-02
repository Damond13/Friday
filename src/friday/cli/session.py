"""会话存储 — JSON 文件持久化"""

import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

SESSIONS_DIR = Path.home() / ".friday" / "sessions"


@dataclass
class Message:
    """对话消息"""

    role: str  # "user" | "assistant"
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Message":
        return cls(role=data["role"], content=data["content"])


@dataclass
class Session:
    """对话会话"""

    id: str = ""
    created_at: str = ""
    messages: list[Message] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "summary": self.summary,
            "messages": [m.to_dict() for m in self.messages],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        return cls(
            id=data["id"],
            created_at=data["created_at"],
            summary=data.get("summary", ""),
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
        )

    def to_messages(self) -> list[dict[str, str]]:
        """转换为 LLM adapter 兼容的 messages 格式"""
        return [m.to_dict() for m in self.messages]

    def add_message(self, role: str, content: str) -> None:
        """添加消息并更新摘要"""
        self.messages.append(Message(role=role, content=content))
        if role == "user" and not self.summary:
            self.summary = content[:50]


def create_session() -> Session:
    """创建新会话"""
    import uuid
    return Session(
        id=uuid.uuid4().hex[:8],
        created_at=datetime.now().isoformat(timespec="seconds"),
    )


def save_session(session: Session) -> Path:
    """保存会话到 JSON 文件，返回文件路径"""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSIONS_DIR / f"{session.id}.json"
    path.write_text(json.dumps(session.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_session(session_id: str) -> Session:
    """按 ID 加载会话，文件不存在时抛出 FileNotFoundError"""
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"会话文件不存在: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return Session.from_dict(data)


def list_sessions() -> list[dict[str, Any]]:
    """按时间倒序列出所有历史会话摘要"""
    if not SESSIONS_DIR.exists():
        return []
    sessions: list[dict[str, Any]] = []
    for f in SESSIONS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sessions.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return sessions[:20]
