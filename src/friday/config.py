"""全局配置加载器，读取 ~/.friday/config.yaml"""

from pathlib import Path
from dataclasses import dataclass, field

import yaml


CONFIG_DIR = Path.home() / ".friday"
CONFIG_PATH = CONFIG_DIR / "config.yaml"

# 各 provider 的默认 base_url
PROVIDER_BASE_URLS: dict[str, str] = {
    "zhipu": "https://open.bigmodel.cn/api/paas/v4/",
    "deepseek": "https://api.deepseek.com",
}


@dataclass
class ProviderConfig:
    """单个 LLM 提供商的配置"""

    name: str
    base_url: str
    api_key: str
    model: str
    max_tokens: int = 4096


@dataclass
class LLMConfig:
    """LLM 模块总配置"""

    provider: str
    providers: dict[str, ProviderConfig] = field(default_factory=dict)


@dataclass
class AppConfig:
    """应用全局配置"""

    llm: LLMConfig | None = None


def _build_provider_config(name: str, raw: dict) -> ProviderConfig:
    """从 YAML 片段构建 ProviderConfig"""
    return ProviderConfig(
        name=name,
        base_url=PROVIDER_BASE_URLS.get(name, raw.get("base_url", "")),
        api_key=raw["api_key"],
        model=raw["model"],
        max_tokens=raw.get("max_tokens", 4096),
    )


def load_config() -> AppConfig:
    """加载 ~/.friday/config.yaml，返回 AppConfig"""
    if not CONFIG_PATH.exists():
        return AppConfig()

    with open(CONFIG_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    llm_raw = raw.get("llm")
    if not llm_raw:
        return AppConfig()

    providers = {
        name: _build_provider_config(name, cfg)
        for name, cfg in llm_raw.get("providers", {}).items()
    }

    return AppConfig(
        llm=LLMConfig(
            provider=llm_raw.get("provider", ""),
            providers=providers,
        ),
    )


def get_llm_config() -> LLMConfig:
    """获取 LLM 配置，未配置时抛出友好错误"""
    config = load_config()
    if config.llm is None:
        raise ValueError(
            f"LLM 未配置，请编辑 {CONFIG_PATH} 添加 API Key"
        )
    return config.llm
