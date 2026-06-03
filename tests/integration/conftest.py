"""集成测试共享 fixture 和跳过逻辑"""

import pytest
from pathlib import Path


def _llm_available() -> bool:
    """检查 LLM 配置是否就绪"""
    config_path = Path.home() / ".friday" / "config.yaml"
    if not config_path.exists():
        return False
    try:
        from friday.config import get_llm_config
        get_llm_config()
        return True
    except ValueError:
        return False


requires_llm = pytest.mark.skipif(
    not _llm_available(),
    reason="需要 LLM API 配置 (~/.friday/config.yaml)",
)
