# 数据模型：CLI 交互壳

**功能分支**: `002-cli-shell` | **日期**: 2026-06-02

## 实体定义

### Session（会话）

```python
@dataclass
class Session:
    id: str                    # UUID，会话唯一标识
    created_at: str            # ISO 格式创建时间
    messages: list[Message]    # 对话消息列表
    summary: str               # 首句摘要（用于 /history 显示）
```

- 存储路径：`~/.friday/sessions/{id}.json`
- 生命周期：创建于 REPL 启动时，`/save` 或 exit 时持久化
- `/history` 按时间倒序列出所有 JSON 文件

### Message（消息）

```python
@dataclass
class Message:
    role: str       # "user" | "assistant"
    content: str    # 消息文本内容
```

- 直接映射为 `list[dict]` 格式，与 LLM adapter 的 `chat()` / `chat_stream()` 接口兼容
- 不需要额外字段（时间戳、ID 等），保持与 OpenAI messages 格式一致

### SlashCommand（斜杠命令）

```python
@dataclass
class SlashCommand:
    name: str                           # 命令名（如 "help", "save"）
    description: str                    # 简要说明
    handler: Callable[[Session], None]  # 执行函数
```

- 通过注册表模式管理，易于扩展
- 不持久化，运行时静态定义

## 实体关系

```text
Session 1──* Message

SlashCommand（独立，无关联）
```

## 存储格式

Session JSON 文件示例：

```json
{
  "id": "a1b2c3d4",
  "created_at": "2026-06-02T14:30:00",
  "summary": "用户问了一个关于天气的问题",
  "messages": [
    {"role": "user", "content": "今天天气怎么样"},
    {"role": "assistant", "content": "我无法实时获取天气数据..."}
  ]
}
```

## 验证规则

- Session.id 必须唯一（UUID 生成）
- Message.role 只能是 "user" 或 "assistant"
- Session.summary 为用户第一条消息的截断（前 50 字符）
- 会话文件数量无上限，`/history` 分页显示（每页 20 条）
