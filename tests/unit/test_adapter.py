"""LLM Adapter 单元测试 — mock OpenAI SDK"""

import json
from unittest.mock import patch, MagicMock

import pytest

from friday.llm.adapter import (
    chat,
    chat_stream,
    get_client,
    get_current_model,
    get_current_provider,
    switch_provider,
    LLMConnectionError,
    LLMAuthError,
    LLMResponseError,
    LLMResponse,
    ToolCall,
    TokenUsage,
)


# ── 测试用的配置 fixture ───────────────────────────────

MOCK_CONFIG = {
    "llm": {
        "provider": "zhipu",
        "providers": {
            "zhipu": {
                "api_key": "test-zhipu-key",
                "model": "glm-4-flash",
                "max_tokens": 4096,
            },
            "deepseek": {
                "api_key": "test-deepseek-key",
                "model": "deepseek-chat",
                "max_tokens": 4096,
            },
        },
    }
}


def _mock_openai_response(content="你好！", tool_calls=None, usage=None):
    """构造 mock 的 OpenAI SDK 响应"""
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls

    choice = MagicMock()
    choice.message = message

    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    return resp


def _mock_usage(prompt=10, completion=20, total=30):
    u = MagicMock()
    u.prompt_tokens = prompt
    u.completion_tokens = completion
    u.total_tokens = total
    return u


# ── get_client 测试 ────────────────────────────────────


@patch("friday.llm.adapter.get_llm_config")
@patch("friday.llm.adapter.OpenAI")
def test_get_client_returns_openai_instance(mock_openai_cls, mock_get_config):
    """get_client() 应返回 OpenAI client 实例"""
    mock_get_config.return_value = MagicMock(
        provider="zhipu",
        providers={
            "zhipu": MagicMock(
                name="zhipu",
                base_url="https://open.bigmodel.cn/api/paas/v4/",
                api_key="test-key",
                model="glm-4-flash",
                max_tokens=4096,
            ),
        },
    )

    # 清除 client 缓存
    import friday.llm.adapter as adapter_mod
    adapter_mod._client_cache.clear()
    adapter_mod._current_provider = ""

    client = get_client()
    mock_openai_cls.assert_called_once_with(
        base_url="https://open.bigmodel.cn/api/paas/v4/",
        api_key="test-key",
    )
    assert client is not None


@patch("friday.llm.adapter.get_llm_config")
def test_get_client_unknown_provider(mock_get_config):
    """请求不存在的 provider 应抛出 ValueError"""
    mock_get_config.return_value = MagicMock(
        provider="zhipu",
        providers={"zhipu": MagicMock()},
    )

    with pytest.raises(ValueError, match="未知的 provider"):
        get_client("nonexistent")


# ── chat 测试 ──────────────────────────────────────────


@patch("friday.llm.adapter.get_llm_config")
@patch("friday.llm.adapter.get_client")
def test_chat_basic(mock_get_client, mock_get_config):
    """基础对话：发送消息，返回文本回复"""
    _setup_mock_config(mock_get_config)

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    usage = _mock_usage()
    mock_client.chat.completions.create.return_value = _mock_openai_response(
        content="你好！我是 Friday。", usage=usage
    )

    resp = chat([{"role": "user", "content": "你好"}])

    assert isinstance(resp, LLMResponse)
    assert resp.content == "你好！我是 Friday。"
    assert resp.usage.total_tokens == 30


@patch("friday.llm.adapter.get_llm_config")
@patch("friday.llm.adapter.get_client")
def test_chat_with_model_override(mock_get_client, mock_get_config):
    """chat() 的 model 参数应覆盖默认模型"""
    _setup_mock_config(mock_get_config)

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_openai_response()

    chat([{"role": "user", "content": "test"}], model="glm-5.1")

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "glm-5.1"


@patch("friday.llm.adapter.get_llm_config")
@patch("friday.llm.adapter.get_client")
def test_chat_with_tool_calls(mock_get_client, mock_get_config):
    """chat() 应正确解析 tool_calls"""
    _setup_mock_config(mock_get_config)

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    tc = MagicMock()
    tc.id = "call_123"
    tc.function.name = "shell_execute"
    tc.function.arguments = '{"command": "ls"}'

    mock_client.chat.completions.create.return_value = _mock_openai_response(
        content=None, tool_calls=[tc]
    )

    resp = chat([{"role": "user", "content": "列一下当前目录"}])

    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].name == "shell_execute"
    assert resp.tool_calls[0].arguments == {"command": "ls"}


# ── 异常包装测试 ────────────────────────────────────────


@patch("friday.llm.adapter.get_llm_config")
@patch("friday.llm.adapter.get_client")
def test_chat_connection_error(mock_get_client, mock_get_config):
    """网络错误应包装为 LLMConnectionError"""
    _setup_mock_config(mock_get_config)
    from openai import APIConnectionError

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.chat.completions.create.side_effect = APIConnectionError(
        request=MagicMock()
    )

    with pytest.raises(LLMConnectionError):
        chat([{"role": "user", "content": "test"}])


@patch("friday.llm.adapter.get_llm_config")
@patch("friday.llm.adapter.get_client")
def test_chat_auth_error(mock_get_client, mock_get_config):
    """认证错误应包装为 LLMAuthError"""
    _setup_mock_config(mock_get_config)
    from openai import AuthenticationError

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.chat.completions.create.side_effect = AuthenticationError(
        message="Invalid API key",
        response=MagicMock(),
        body=None,
    )

    with pytest.raises(LLMAuthError):
        chat([{"role": "user", "content": "test"}])


# ── switch_provider 测试 ────────────────────────────────


@patch("friday.llm.adapter.get_llm_config")
def test_switch_provider(mock_get_config):
    """switch_provider 应切换当前 provider"""
    _setup_mock_config(mock_get_config)

    import friday.llm.adapter as adapter_mod
    adapter_mod._current_provider = ""

    switch_provider("deepseek")
    assert get_current_provider() == "deepseek"


@patch("friday.llm.adapter.get_llm_config")
def test_switch_provider_unknown(mock_get_config):
    """切换到不存在的 provider 应抛出 ValueError"""
    _setup_mock_config(mock_get_config)

    with pytest.raises(ValueError, match="未知的 provider"):
        switch_provider("nonexistent")


@patch("friday.llm.adapter.get_llm_config")
def test_get_current_model(mock_get_config):
    """get_current_model 应返回当前 provider 的模型"""
    _setup_mock_config(mock_get_config)

    import friday.llm.adapter as adapter_mod
    adapter_mod._current_provider = ""

    assert get_current_model() == "glm-4-flash"


# ── chat_stream 测试 ───────────────────────────────────


@patch("friday.llm.adapter.get_llm_config")
@patch("friday.llm.adapter.get_client")
def test_chat_stream(mock_get_client, mock_get_config):
    """chat_stream 应逐 token 返回文本"""
    _setup_mock_config(mock_get_config)

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # 构造 stream mock
    chunks = []
    for text in ["你", "好", "！"]:
        delta = MagicMock()
        delta.content = text
        choice = MagicMock()
        choice.delta = delta
        chunk = MagicMock()
        chunk.choices = [choice]
        chunks.append(chunk)

    mock_client.chat.completions.create.return_value = iter(chunks)

    result = list(chat_stream([{"role": "user", "content": "你好"}]))

    assert result == ["你", "好", "！"]


# ── 辅助函数 ────────────────────────────────────────────


def _setup_mock_config(mock_get_config):
    """为 mock_get_config 设置标准返回值"""
    mock_get_config.return_value = MagicMock(
        provider="zhipu",
        providers={
            "zhipu": MagicMock(
                name="zhipu",
                base_url="https://open.bigmodel.cn/api/paas/v4/",
                api_key="test-key",
                model="glm-4-flash",
                max_tokens=4096,
            ),
            "deepseek": MagicMock(
                name="deepseek",
                base_url="https://api.deepseek.com",
                api_key="test-key2",
                model="deepseek-chat",
                max_tokens=4096,
            ),
        },
    )
