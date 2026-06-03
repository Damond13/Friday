"""单元测试：共享 Embedding 模型实例"""

from unittest.mock import MagicMock, patch

import pytest


def test_get_shared_model_returns_cached_instance():
    """get_shared_model() 多次调用返回同一实例"""
    from friday.knowledge import embedding as emb_module
    emb_module._get_model.cache_clear()

    with patch("sentence_transformers.SentenceTransformer") as MockST:
        mock_instance = MagicMock()
        MockST.return_value = mock_instance

        model1 = emb_module.get_shared_model()
        model2 = emb_module.get_shared_model()

        assert model1 is model2
        MockST.assert_called_once()


def test_mem0_uses_shared_model():
    """Mem0 初始化后，内部模型被替换为共享实例"""
    from friday.knowledge import embedding as emb_module
    emb_module._get_model.cache_clear()

    shared_model = MagicMock()
    memory_instance = MagicMock()
    memory_instance.embedding_model.model = MagicMock()

    with patch("sentence_transformers.SentenceTransformer", return_value=shared_model), \
         patch("mem0.Memory") as MockMemory:
        MockMemory.from_config.return_value = memory_instance

        from friday.memory import dynamic as dyn_module
        dyn_module._memory_instance = None

        with patch.object(dyn_module, "_build_llm_config", return_value=None):
            m = dyn_module._get_memory()

        assert memory_instance.embedding_model.model is emb_module.get_shared_model()


def test_mem0_injection_failure_does_not_break_init():
    """模型注入失败不应导致 Mem0 初始化失败"""
    from friday.knowledge import embedding as emb_module
    emb_module._get_model.cache_clear()

    memory_instance = MagicMock()
    type(memory_instance.embedding_model).model = property(
        lambda self: MagicMock(),
        lambda self, val: (_ for _ in ()).throw(RuntimeError("injection failed")),
    )

    with patch("sentence_transformers.SentenceTransformer", return_value=MagicMock()), \
         patch("mem0.Memory") as MockMemory:
        MockMemory.from_config.return_value = memory_instance

        from friday.memory import dynamic as dyn_module
        dyn_module._memory_instance = None

        with patch.object(dyn_module, "_build_llm_config", return_value=None):
            m = dyn_module._get_memory()

        assert m is not None
