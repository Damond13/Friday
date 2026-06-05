"""ChromaDB 向量索引管理"""

import logging
from pathlib import Path

import chromadb

from friday.knowledge.store import SearchResult

logger = logging.getLogger(__name__)

_CHROMA_DIR = Path.home() / ".friday" / "knowledge" / "chroma"
_COLLECTION_NAME = "friday_notes"

_client: chromadb.ClientAPI | None = None


def _get_client(chroma_dir: Path | None = None) -> chromadb.ClientAPI:
    """获取或创建 ChromaDB PersistentClient"""
    global _client
    if _client is not None:
        return _client
    path = chroma_dir or _CHROMA_DIR
    path.mkdir(parents=True, exist_ok=True)
    _client = chromadb.PersistentClient(path=str(path))
    return _client


def _get_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    """获取或创建 collection，维度不匹配时自动重建"""
    from friday.knowledge.embedding import get_embedding_dim
    expected_dim = get_embedding_dim()
    collection = client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine", "embedding_dim": expected_dim},
    )
    stored_dim = collection.metadata.get("embedding_dim")
    if stored_dim == expected_dim:
        return collection
    if stored_dim is not None:
        logger.warning("Collection 维度不匹配 (存储=%s, 当前=%d)，自动重建", stored_dim, expected_dim)
    else:
        logger.warning("Collection 无维度标记，自动重建")
    client.delete_collection(_COLLECTION_NAME)
    return client.create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine", "embedding_dim": expected_dim},
    )


def init_vector(chroma_dir: Path | None = None) -> chromadb.ClientAPI:
    """初始化 ChromaDB，返回客户端"""
    client = _get_client(chroma_dir)
    _get_collection(client)
    return client


def upsert(note_id: str, content: str, title: str = "",
           tags: list[str] | None = None, file_path: str = "") -> None:
    """插入或更新向量"""
    from friday.knowledge.embedding import embed_text
    client = _get_client()
    collection = _get_collection(client)
    embedding = embed_text(content)
    metadata = {"title": title, "tags": ", ".join(tags or []), "file_path": file_path}
    collection.upsert(
        ids=[note_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[metadata],
    )


def delete(note_id: str) -> None:
    """删除向量"""
    client = _get_client()
    collection = _get_collection(client)
    collection.delete(ids=[note_id])


def search(query: str, limit: int = 5) -> list[SearchResult]:
    """语义搜索"""
    from friday.knowledge.embedding import embed_text
    client = _get_client()
    collection = _get_collection(client)
    query_embedding = embed_text(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        include=["documents", "metadatas", "distances"],
    )
    if not results["ids"] or not results["ids"][0]:
        return []
    search_results: list[SearchResult] = []
    for i, note_id in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i] if results["metadatas"] else {}
        doc = results["documents"][0][i] if results["documents"] else ""
        dist = results["distances"][0][i] if results["distances"] else 0.0
        search_results.append(SearchResult(
            note_id=note_id,
            title=meta.get("title", ""),
            snippet=doc[:100] + ("..." if len(doc) > 100 else ""),
            score=1.0 - dist,
            source="vector",
            file_path=meta.get("file_path", ""),
        ))
    return search_results


def reset_client() -> None:
    """重置客户端缓存（用于测试）"""
    global _client
    _client = None
