"""动态记忆 — Mem0 封装"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from friday.config import CONFIG_DIR, get_llm_config

logger = logging.getLogger(__name__)

MEMORY_DIR = CONFIG_DIR.parent / ".friday-memory"

_memory_instance: Any = None


@dataclass
class MemoryItem:
    """动态记忆条目"""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


@dataclass
class MemorySearchResult:
    """统一检索结果"""

    source: str  # "dynamic" / "files"
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


def _get_memory() -> Any:
    """获取或初始化 Mem0 实例"""
    global _memory_instance
    if _memory_instance is not None:
        return _memory_instance
    _memory_instance = _init_memory()
    return _memory_instance


def _init_memory() -> Any:
    """初始化 Mem0，配置本地 ChromaDB"""
    try:
        from mem0 import Memory

        llm_config = _build_llm_config()
        config: dict[str, Any] = {
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "friday_memories",
                    "path": str(MEMORY_DIR),
                },
            },
        }
        if llm_config:
            config["llm"] = llm_config

        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        return Memory.from_config(config)
    except Exception as exc:
        logger.warning("Mem0 初始化失败，动态记忆不可用: %s", exc)
        return None


def _build_llm_config() -> dict[str, Any] | None:
    """从 Friday 配置构建 Mem0 LLM 配置"""
    try:
        llm = get_llm_config()
        provider_cfg = llm.providers.get(llm.provider)
        if not provider_cfg:
            return None
        return {
            "provider": "openai",
            "config": {
                "model": provider_cfg.model,
                "api_key": provider_cfg.api_key,
                "openai_base_url": provider_cfg.base_url,
            },
        }
    except (ValueError, KeyError):
        return None


def add_memory(content: str, metadata: dict[str, Any] | None = None) -> MemoryItem:
    """添加一条动态记忆"""
    m = _get_memory()
    if m is None:
        raise RuntimeError("动态记忆服务不可用")

    result = m.add(content, user_id="friday_user", metadata=metadata or {})
    memory_id = _extract_id(result)
    return MemoryItem(id=memory_id, content=content, metadata=metadata or {})


def search_memory(query: str, limit: int = 10) -> list[MemorySearchResult]:
    """语义检索动态记忆"""
    m = _get_memory()
    if m is None:
        return []

    results = m.search(query=query, user_id="friday_user", limit=limit)
    items: list[MemorySearchResult] = []
    for r in results:
        items.append(MemorySearchResult(
            source="dynamic",
            content=r.get("memory", ""),
            score=r.get("score", 0.0),
            metadata=r.get("metadata", {}),
        ))
    return items


def list_memories() -> list[MemoryItem]:
    """列出所有动态记忆"""
    m = _get_memory()
    if m is None:
        return []

    results = m.get_all(user_id="friday_user")
    items: list[MemoryItem] = []
    for r in results:
        items.append(MemoryItem(
            id=r.get("id", ""),
            content=r.get("memory", ""),
            metadata=r.get("metadata", {}),
        ))
    return items


def delete_memory(memory_id: str) -> bool:
    """删除指定动态记忆"""
    m = _get_memory()
    if m is None:
        return False

    try:
        m.delete(memory_id)
        return True
    except Exception as exc:
        logger.warning("删除记忆失败 %s: %s", memory_id, exc)
        return False


def _extract_id(result: Any) -> str:
    """从 Mem0 add() 结果中提取记忆 ID"""
    if isinstance(result, dict):
        results = result.get("results", [])
        if results and isinstance(results, list):
            return results[0].get("id", "")
    return ""
