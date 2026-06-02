# Research: LLM 统一适配层

## 决策 1: 统一适配方案

**选择**: OpenAI SDK 直接适配器
**原因**: 智谱和 DeepSeek 都 100% 兼容 OpenAI 格式，只需切换 base_url
**备选**:
- litellm（100+ provider）— 对 2 provider 场景过重，引入 proxy server 等不必要组件
- mirascope — Pythonic 但不原生支持智谱

## 决策 2: 智谱 API 兼容性

**结论**: 完全兼容 OpenAI 格式
**Base URL**: `https://open.bigmodel.cn/api/paas/v4/`
**SDK**: 可用 openai SDK 直接连接，或用官方 zhipuai SDK
**功能支持**: function calling ✅ | streaming ✅ | tool use ✅
**模型**: glm-4.5, glm-4.6, glm-4.7, glm-5

## 决策 3: DeepSeek API 兼容性

**结论**: 完全兼容 OpenAI 格式
**Base URL**: `https://api.deepseek.com`
**SDK**: 直接用 openai SDK，无需独立 SDK
**功能支持**: function calling ✅ | streaming ✅ | tool use ✅
**模型**: deepseek-chat (V3.2), deepseek-reasoner (R1)

## 决策 4: 依赖选择

**选择**: openai SDK（唯一 LLM 依赖）
**原因**: 两个 provider 都用同一个 SDK，零额外适配成本
**备选**:
- zhipuai SDK — 引入不必要的额外依赖，功能与 openai SDK 重复
- litellm — 过度工程，违背"简洁实用"原则

## 决策 5: 配置管理

**选择**: YAML 配置文件（~/.friday/config.yaml）
**原因**: 人可读，易手动编辑，与项目其他配置统一
**格式**:
```yaml
llm:
  provider: zhipu  # 当前使用的 provider
  providers:
    zhipu:
      api_key: "xxx"
      model: "glm-4-flash"
      max_tokens: 4096
    deepseek:
      api_key: "xxx"
      model: "deepseek-chat"
      max_tokens: 4096
```
