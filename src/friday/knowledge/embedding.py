"""本地 Embedding Adapter — BAAI/bge-m3 模型"""

import os
from functools import lru_cache

_EMBEDDING_DIM = 1024
_MODEL_NAME = "BAAI/bge-m3"


@lru_cache(maxsize=1)
def _get_model():
    """延迟加载 sentence-transformers 模型，离线模式避免 HuggingFace 超时"""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(_MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """将文本列表转为向量列表（1024 维）"""
    if not texts:
        return []
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return [e.tolist() for e in embeddings]


def embed_text(text: str) -> list[float]:
    """将单条文本转为向量"""
    return embed_texts([text])[0]


def get_embedding_dim() -> int:
    """返回向量维度"""
    return _EMBEDDING_DIM
