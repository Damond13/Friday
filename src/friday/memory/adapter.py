"""双层记忆系统 — 统一接口"""

from typing import Any

from friday.memory.dynamic import (
    MemoryItem,
    MemorySearchResult,
    add_memory as _add_dynamic,
    search_memory as _search_dynamic,
    list_memories as _list_dynamic,
    delete_memory as _delete_dynamic,
)
from friday.memory.files import (
    Decision,
    Lesson,
    add_decision as _add_decision,
    list_decisions as _list_decisions,
    add_lesson as _add_lesson,
    list_lessons as _list_lessons,
    get_constitution as _get_constitution,
    search_files as _search_files,
)


def add_memory(content: str, metadata: dict[str, Any] | None = None) -> MemoryItem:
    """添加一条动态记忆"""
    return _add_dynamic(content, metadata)


def search_memories(query: str, limit: int = 10) -> list[MemorySearchResult]:
    """统一搜索两层记忆：动态记忆 + 文件记忆"""
    dynamic_results = _search_dynamic(query, limit)
    file_results = _search_files(query)
    combined = dynamic_results + file_results
    combined.sort(key=lambda r: r.score, reverse=True)
    return combined[:limit]


def list_memories() -> list[MemoryItem]:
    """列出所有动态记忆"""
    return _list_dynamic()


def delete_memory(memory_id: str) -> bool:
    """删除指定动态记忆"""
    return _delete_dynamic(memory_id)


def add_decision(
    title: str, decision: str, context: str = "", status: str = "已采纳"
) -> Decision:
    """添加一条决策记录"""
    return _add_decision(title, decision, context, status)


def list_decisions() -> list[Decision]:
    """列出所有决策记录"""
    return _list_decisions()


def add_lesson(title: str, lesson: str, context: str = "") -> Lesson:
    """添加一条经验教训"""
    return _add_lesson(title, lesson, context)


def list_lessons() -> list[Lesson]:
    """列出所有经验教训"""
    return _list_lessons()


def get_constitution() -> str:
    """读取项目宪法内容"""
    return _get_constitution()
