"""笔记文件管理 — Markdown 文件存储与数据类"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

KNOWLEDGE_DIR = Path.home() / ".friday" / "knowledge"
NOTES_DIR = KNOWLEDGE_DIR / "notes"


@dataclass
class Note:
    """一条知识笔记"""

    id: str = ""
    title: str = ""
    content: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    file_path: Path = field(default_factory=Path)

    def to_markdown(self) -> str:
        """序列化为带 YAML front matter 的 Markdown"""
        tags_str = ", ".join(self.tags) if self.tags else ""
        return (
            f"---\n"
            f"id: {self.id}\n"
            f"title: {self.title}\n"
            f"tags: [{tags_str}]\n"
            f"created_at: {self.created_at}\n"
            f"---\n\n"
            f"{self.content}\n"
        )

    @classmethod
    def from_markdown(cls, text: str, file_path: Path) -> "Note":
        """从 Markdown 文本解析 Note"""
        meta = _parse_front_matter(text)
        body = _strip_front_matter(text)
        return cls(
            id=meta.get("id", ""),
            title=meta.get("title", ""),
            content=body.strip(),
            tags=meta.get("tags", []),
            created_at=meta.get("created_at", ""),
            file_path=file_path,
        )


@dataclass
class SearchResult:
    """检索结果"""

    note_id: str = ""
    title: str = ""
    snippet: str = ""
    score: float = 0.0
    source: str = ""  # "fts" | "vector" | "rag"
    file_path: str = ""


def _parse_front_matter(text: str) -> dict:
    """解析 YAML front matter 为字典"""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    result: dict = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if key == "tags":
            result[key] = _parse_tags(value)
        else:
            result[key] = value.strip("'\"")
    return result


def _parse_tags(value: str) -> list[str]:
    """解析 [tag1, tag2] 格式的标签列表"""
    value = value.strip().strip("[]")
    if not value:
        return []
    return [t.strip().strip("'\"") for t in value.split(",") if t.strip()]


def _strip_front_matter(text: str) -> str:
    """移除 front matter，返回正文"""
    match = re.match(r"^---\s*\n.*?\n---\s*\n?", text, re.DOTALL)
    if not match:
        return text
    return text[match.end():]


def validate_note_id(note_id: str) -> str:
    """校验 note_id 只含十六进制字符，防止路径遍历"""
    if not re.fullmatch(r"[0-9a-f]+", note_id):
        raise ValueError(f"无效的 note_id: {note_id}")
    return note_id


def create_note_file(note: Note) -> Path:
    """将 Note 写入 Markdown 文件，返回文件路径"""
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    path = NOTES_DIR / f"{note.id}.md"
    path.write_text(note.to_markdown(), encoding="utf-8")
    note.file_path = path
    return path


def read_note_file(path: Path) -> Note:
    """读取 Markdown 文件并解析为 Note"""
    text = path.read_text(encoding="utf-8")
    return Note.from_markdown(text, path)


def delete_note_file(note_id: str) -> bool:
    """删除笔记文件，返回是否成功"""
    validate_note_id(note_id)
    path = NOTES_DIR / f"{note_id}.md"
    if path.exists():
        path.unlink()
        return True
    return False


def list_note_files() -> list[Path]:
    """列出所有笔记文件路径"""
    if not NOTES_DIR.exists():
        return []
    return sorted(NOTES_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)


def generate_note_id() -> str:
    """生成笔记 ID"""
    import uuid
    return uuid.uuid4().hex[:8]


def now_iso() -> str:
    """当前时间的 ISO 格式字符串"""
    return datetime.now().isoformat(timespec="seconds")
