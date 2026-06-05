"""本地 Embedding Adapter — BAAI/bge-small-zh-v1.5 模型"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

_EMBEDDING_DIM = 512
_MODEL_NAME = "BAAI/bge-small-zh-v1.5"


@lru_cache(maxsize=1)
def _get_model():
    """延迟加载 sentence-transformers 模型，离线模式避免 HuggingFace 超时"""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(_MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """将文本列表转为向量列表（512 维）"""
    if not texts:
        return []
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return [e.tolist() for e in embeddings]


def embed_text(text: str) -> list[float]:
    """将单条文本转为向量"""
    return embed_texts([text])[0]


def get_shared_model() -> SentenceTransformer:
    """获取共享的 SentenceTransformer 模型实例（供外部模块复用）"""
    return _get_model()


def get_embedding_dim() -> int:
    """返回向量维度"""
    return _EMBEDDING_DIM
