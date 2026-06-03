"""集成测试 — 配置加载与验证"""

from pathlib import Path

import pytest

from friday.config import (
    AppConfig,
    LLMConfig,
    ProviderConfig,
    CONFIG_PATH,
    get_llm_config,
    load_config,
    PROVIDER_BASE_URLS,
)


class TestConfigLoading:
    """配置文件加载"""

    def test_config_file_exists(self) -> None:
        """~/.friday/config.yaml 存在"""
        assert CONFIG_PATH.exists(), f"配置文件不存在: {CONFIG_PATH}"

    def test_load_config_returns_app_config(self) -> None:
        """load_config 返回有效的 AppConfig"""
        config = load_config()
        assert isinstance(config, AppConfig)
        assert config.llm is not None

    def test_get_llm_config_returns_llm_config(self) -> None:
        """get_llm_config 返回有效的 LLMConfig"""
        llm = get_llm_config()
        assert isinstance(llm, LLMConfig)
        assert llm.provider
        assert llm.providers

    def test_provider_has_required_fields(self) -> None:
        """每个 provider 配置包含必要字段"""
        llm = get_llm_config()
        for name, pcfg in llm.providers.items():
            assert isinstance(pcfg, ProviderConfig)
            assert pcfg.api_key, f"provider {name} 缺少 api_key"
            assert pcfg.model, f"provider {name} 缺少 model"
            assert pcfg.base_url, f"provider {name} 缺少 base_url"

    def test_active_provider_in_providers(self) -> None:
        """当前 provider 名称在 providers 字典中"""
        llm = get_llm_config()
        assert llm.provider in llm.providers

    def test_base_url_auto_fill(self) -> None:
        """已知 provider 自动填充 base_url"""
        llm = get_llm_config()
        for name, pcfg in llm.providers.items():
            if name in PROVIDER_BASE_URLS:
                assert pcfg.base_url == PROVIDER_BASE_URLS[name]

    def test_max_tokens_default(self) -> None:
        """max_tokens 有合理默认值"""
        llm = get_llm_config()
        for pcfg in llm.providers.values():
            assert pcfg.max_tokens > 0
