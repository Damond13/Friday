"""动态记忆系统 — 统一接口"""

from typing import Any

from friday.memory.dynamic import (
    MemoryItem,
    MemorySearchResult,
    add_memory as _add_dynamic,
    search_memory as _search_dynamic,
    list_memories as _list_dynamic,
    delete_memory as _delete_dynamic,
)


def add_memory(content: str, metadata: dict[str, Any] | None = None) -> MemoryItem:
    """添加一条动态记忆"""
    return _add_dynamic(content, metadata)


def search_memories(query: str, limit: int = 10) -> list[MemorySearchResult]:
    """语义检索动态记忆"""
    return _search_dynamic(query, limit)


def list_memories() -> list[MemoryItem]:
    """列出所有动态记忆"""
    return _list_dynamic()


def delete_memory(memory_id: str) -> bool:
    """删除指定动态记忆"""
    return _delete_dynamic(memory_id)
