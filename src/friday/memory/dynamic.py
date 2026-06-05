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
    """初始化 Mem0，配置本地 ChromaDB + HuggingFace embedding"""
    try:
        import os
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("MEM0_TELEMETRY", "False")

        from mem0 import Memory

        llm_config = _build_llm_config()
        config: dict[str, Any] = {
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": "BAAI/bge-small-zh-v1.5",
                },
            },
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
        memory = Memory.from_config(config)

        # 用共享实例替换 Mem0 内部模型，省掉一份内存
        # 注意：embedding_model.model 是 Mem0 (mem0ai>=0.1.0) 未文档化的内部属性，
        # 若 Mem0 升级后属性路径变更，try/except 会降级为独立模型
        try:
            from friday.knowledge.embedding import get_shared_model
            memory.embedding_model.model = get_shared_model()
            logger.info("已将 Mem0 内部模型替换为共享实例")
        except Exception as inject_exc:
            logger.warning("共享模型注入失败，Mem0 使用独立模型: %s", inject_exc)

        return memory
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

    raw = m.search(query=query, limit=limit, filters={"user_id": "friday_user"})
    results = raw.get("results", []) if isinstance(raw, dict) else raw
    items: list[MemorySearchResult] = []
    for r in results:
        items.append(MemorySearchResult(
            source="dynamic",
            content=r.get("memory", "") if isinstance(r, dict) else str(r),
            score=r.get("score", 0.0) if isinstance(r, dict) else 0.0,
            metadata=r.get("metadata", {}) if isinstance(r, dict) else {},
        ))
    return items


def list_memories() -> list[MemoryItem]:
    """列出所有动态记忆"""
    m = _get_memory()
    if m is None:
        return []

    raw = m.get_all(filters={"user_id": "friday_user"})
    results = raw.get("results", []) if isinstance(raw, dict) else raw
    items: list[MemoryItem] = []
    for r in results:
        items.append(MemoryItem(
            id=r.get("id", "") if isinstance(r, dict) else "",
            content=r.get("memory", "") if isinstance(r, dict) else str(r),
            metadata=r.get("metadata", {}) if isinstance(r, dict) else {},
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
