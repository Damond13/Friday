"""LLM 统一适配层 — 基于 OpenAI SDK 兼容智谱/DeepSeek"""

import json
from collections.abc import Iterator
from contextlib import contextmanager

from openai import OpenAI, APIConnectionError, AuthenticationError, APIStatusError

from friday.config import ProviderConfig, get_llm_config
from friday.llm.prompts import PromptContext, build_system_prompt
from friday.llm.types import LLMResponse, TokenUsage, ToolCall


class LLMError(Exception):
    """LLM 调用异常基类"""

class LLMConnectionError(LLMError):
    """网络连接失败或 API 超时"""

class LLMAuthError(LLMError):
    """API Key 无效或未配置"""

class LLMResponseError(LLMError):
    """返回格式异常"""


_current_provider: str = ""
_client_cache: dict[str, OpenAI] = {}


@contextmanager
def _wrap_llm_errors():
    """统一包装 OpenAI SDK 异常为自定义异常"""
    try:
        yield
    except APIConnectionError as e:
        raise LLMConnectionError(f"网络连接失败: {e}") from e
    except AuthenticationError as e:
        raise LLMAuthError(f"API Key 无效: {e}") from e
    except APIStatusError as e:
        raise LLMResponseError(f"API 返回错误 ({e.status_code}): {e.message}") from e
    except Exception as e:
        if isinstance(e, LLMError):
            raise
        raise LLMResponseError(f"未知错误: {e}") from e


def get_client(provider: str | None = None) -> OpenAI:
    """获取或创建配置好的 OpenAI client"""
    global _current_provider
    llm = get_llm_config()
    name = provider or _current_provider or llm.provider
    if name not in llm.providers:
        raise ValueError(f"未知的 provider: {name}，可选: {list(llm.providers.keys())}")
    if name in _client_cache:
        return _client_cache[name]
    pcfg: ProviderConfig = llm.providers[name]
    client = OpenAI(base_url=pcfg.base_url, api_key=pcfg.api_key)
    _client_cache[name] = client
    if not _current_provider:
        _current_provider = name
    return client


def chat(
    messages: list[dict],
    tools: list[dict] | None = None,
    model: str | None = None,
    context: PromptContext | None = None,
) -> LLMResponse:
    """发送对话请求，返回统一格式的响应"""
    with _wrap_llm_errors():
        client = get_client()
        pcfg = _get_active_config()
        if context:
            messages = _inject_system_prompt(messages, context)
        kwargs: dict = {"model": model or pcfg.model, "messages": messages, "max_tokens": pcfg.max_tokens}
        if tools:
            kwargs["tools"] = tools
        resp = client.chat.completions.create(**kwargs)
        return _parse_response(resp)


def chat_stream(
    messages: list[dict],
    tools: list[dict] | None = None,
    model: str | None = None,
    context: PromptContext | None = None,
) -> Iterator[str]:
    """流式发送对话请求，逐 token 返回文本"""
    with _wrap_llm_errors():
        client = get_client()
        pcfg = _get_active_config()
        if context:
            messages = _inject_system_prompt(messages, context)
        kwargs: dict = {"model": model or pcfg.model, "messages": messages, "max_tokens": pcfg.max_tokens, "stream": True}
        if tools:
            kwargs["tools"] = tools
        stream = client.chat.completions.create(**kwargs)
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content


def switch_provider(provider: str) -> None:
    """运行时切换 LLM provider"""
    llm = get_llm_config()
    if provider not in llm.providers:
        raise ValueError(f"未知的 provider: {provider}，可选: {list(llm.providers.keys())}")
    global _current_provider
    _current_provider = provider


def get_current_provider() -> str:
    """获取当前使用的 provider 名称"""
    llm = get_llm_config()
    return _current_provider or llm.provider


def get_current_model() -> str:
    """获取当前使用的模型名称"""
    return _get_active_config().model


def _inject_system_prompt(messages: list[dict], context: PromptContext) -> list[dict]:
    """将 context 组装为 system prompt 注入到 messages"""
    system_msg = {"role": "system", "content": build_system_prompt(context)}
    has_system = any(m.get("role") == "system" for m in messages)
    if has_system:
        return [
            {"role": "system", "content": m["content"] + "\n\n" + system_msg["content"]}
            if m.get("role") == "system" else m
            for m in messages
        ]
    return [system_msg] + messages


def _get_active_config() -> ProviderConfig:
    """获取当前活跃的 ProviderConfig"""
    llm = get_llm_config()
    name = _current_provider or llm.provider
    return llm.providers[name]


def _parse_response(resp) -> LLMResponse:
    """将 OpenAI SDK 响应解析为 LLMResponse"""
    choice = resp.choices[0] if resp.choices else None
    if not choice:
        raise LLMResponseError("API 返回空响应")
    message = choice.message
    tool_calls = []
    if message.tool_calls:
        for tc in message.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError as e:
                raise LLMResponseError(f"工具调用参数解析失败: {e}") from e
            tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))
    usage = TokenUsage()
    if resp.usage:
        usage = TokenUsage(
            prompt_tokens=resp.usage.prompt_tokens,
            completion_tokens=resp.usage.completion_tokens,
            total_tokens=resp.usage.total_tokens,
        )
    return LLMResponse(content=message.content or "", tool_calls=tool_calls, usage=usage)
