"""文件记忆 — 结构化 Markdown 管理"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from friday.memory.dynamic import MemorySearchResult

# 项目根目录下的 .specify/memory/
MEMORY_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".specify" / "memory"


@dataclass
class Decision:
    """决策记录"""

    title: str
    date: str
    status: str
    context: str
    decision: str


@dataclass
class Lesson:
    """经验教训"""

    title: str
    date: str
    context: str
    lesson: str


def _now() -> str:
    """当前 ISO 日期"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _read_file(path: Path) -> str:
    """安全读取文件"""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _append_entry(path: Path, entry: str) -> None:
    """追加条目到 Markdown 文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = _read_file(path)
    if content and not content.endswith("\n"):
        content += "\n"
    content = entry + "\n" + content
    path.write_text(content, encoding="utf-8")


def add_decision(
    title: str,
    decision: str,
    context: str = "",
    status: str = "已采纳",
) -> Decision:
    """添加一条决策记录"""
    d = Decision(title=title, date=_now(), status=status, context=context, decision=decision)
    entry = _format_decision(d)
    _append_entry(MEMORY_DIR / "decisions.md", entry)
    return d


def list_decisions() -> list[Decision]:
    """列出所有决策记录，按时间倒序"""
    content = _read_file(MEMORY_DIR / "decisions.md")
    return _parse_decisions(content)


def add_lesson(title: str, lesson: str, context: str = "") -> Lesson:
    """添加一条经验教训"""
    l = Lesson(title=title, date=_now(), context=context, lesson=lesson)
    entry = _format_lesson(l)
    _append_entry(MEMORY_DIR / "lessons-learned.md", entry)
    return l


def list_lessons() -> list[Lesson]:
    """列出所有经验教训，按时间倒序"""
    content = _read_file(MEMORY_DIR / "lessons-learned.md")
    return _parse_lessons(content)


def get_constitution() -> str:
    """读取项目宪法内容"""
    return _read_file(MEMORY_DIR / "constitution.md")


def search_files(query: str) -> list[MemorySearchResult]:
    """关键词搜索文件记忆"""
    results: list[MemorySearchResult] = []
    query_lower = query.lower()

    for path_name, source in [("decisions.md", "files"), ("lessons-learned.md", "files")]:
        content = _read_file(MEMORY_DIR / path_name)
        if not content:
            continue
        if query_lower in content.lower():
            # 提取匹配的条目段落
            sections = re.split(r"^## ", content, flags=re.MULTILINE)
            for section in sections:
                if not section.strip():
                    continue
                if query_lower in section.lower():
                    results.append(MemorySearchResult(
                        source=source,
                        content="## " + section.strip(),
                        score=1.0,
                        metadata={"file": path_name},
                    ))
    return results


def _format_decision(d: Decision) -> str:
    """格式化决策记录为 Markdown"""
    lines = [
        f"## 决策: {d.title}",
        f"**日期**: {d.date}",
        f"**状态**: {d.status}",
    ]
    if d.context:
        lines.append(f"**背景**: {d.context}")
    lines.append(f"**决定**: {d.decision}")
    return "\n".join(lines)


def _format_lesson(l: Lesson) -> str:
    """格式化经验教训为 Markdown"""
    lines = [
        f"## 经验: {l.title}",
        f"**日期**: {l.date}",
    ]
    if l.context:
        lines.append(f"**场景**: {l.context}")
    lines.append(f"**内容**: {l.lesson}")
    return "\n".join(lines)


def _parse_decisions(content: str) -> list[Decision]:
    """解析决策记录文件"""
    decisions: list[Decision] = []
    sections = re.split(r"^## 决策: ", content, flags=re.MULTILINE)
    for section in sections[1:]:
        decisions.append(_parse_one_decision(section))
    return decisions


def _parse_one_decision(text: str) -> Decision:
    """解析单条决策"""
    title = text.split("\n", 1)[0].strip()
    date = _extract_field(text, "日期") or ""
    status = _extract_field(text, "状态") or "已采纳"
    context = _extract_field(text, "背景") or ""
    decision = _extract_field(text, "决定") or ""
    return Decision(title=title, date=date, status=status, context=context, decision=decision)


def _parse_lessons(content: str) -> list[Lesson]:
    """解析经验教训文件"""
    lessons: list[Lesson] = []
    sections = re.split(r"^## 经验: ", content, flags=re.MULTILINE)
    for section in sections[1:]:
        lessons.append(_parse_one_lesson(section))
    return lessons


def _parse_one_lesson(text: str) -> Lesson:
    """解析单条经验"""
    title = text.split("\n", 1)[0].strip()
    date = _extract_field(text, "日期") or ""
    context = _extract_field(text, "场景") or ""
    lesson = _extract_field(text, "内容") or ""
    return Lesson(title=title, date=date, context=context, lesson=lesson)


def _extract_field(text: str, field_name: str) -> str | None:
    """提取 Markdown 字段值"""
    match = re.search(rf"\*\*{field_name}\*\*:\s*(.+)", text)
    return match.group(1).strip() if match else None
