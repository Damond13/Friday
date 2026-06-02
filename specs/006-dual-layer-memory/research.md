# Research: 双层记忆系统技术决策

**Date**: 2026-06-02 | **Branch**: `006-dual-layer-memory`

## R001: Mem0 本地配置方案

**Decision**: 使用 `Memory.from_config()` 配置本地 ChromaDB，LLM 使用 OpenAI 兼容接口连接 Friday 的 LLM provider。

**Rationale**:
- Mem0 已在 pyproject.toml 中作为依赖
- ChromaDB 是 Mem0 内置支持的向量数据库，无需额外安装
- 本地存储路径 `.friday-memory/`，与 CLAUDE.md 一致
- Mem0 需要 LLM 进行记忆提取，使用 OpenAI 兼容接口可接入智谱/DeepSeek

**配置结构**:
```python
config = {
    "llm": {
        "provider": "openai",  # 兼容模式
        "config": {
            "model": "...",
            "api_key": "...",
            "openai_base_url": "...",
        }
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "friday_memories",
            "path": ".friday-memory/"
        }
    }
}
```

**Alternatives considered**:
- Memory() 默认初始化：需要 OPENAI_API_KEY 环境变量，不够灵活
- 自行实现向量存储：工作量大，Mem0 已封装好记忆提取+存储+检索
- 不用 Mem0，纯 ChromaDB：需要自己实现记忆提取逻辑，违背"优先借鉴开源方案"

## R002: 结构化文件记忆的存储格式

**Decision**: 每种记忆类型一个 Markdown 文件，条目按时间倒序排列，使用 YAML front matter 存储元数据。

**文件命名**:
- `constitution.md` — 项目宪法（已有，只读引用）
- `decisions.md` — 架构决策记录
- `lessons-learned.md` — 经验教训

**条目格式**:
```markdown
## 决策: 使用 adapter 模式隔离第三方依赖

**日期**: 2026-06-01
**状态**: 已采纳
**背景**: 需要隔离 LLM SDK 变更对业务逻辑的影响
**决定**: 所有外部调用通过 adapter 层
```

**Rationale**:
- Markdown 人可读，支持 Git diff
- 已有 `.specify/memory/` 目录结构
- 固定文件名便于查找和管理

**Alternatives considered**:
- YAML 文件：不如 Markdown 可读性好
- SQLite 存储：不利于 Git 管理和人工编辑
- 每条决策一个文件：文件过多，不便于浏览

## R003: 统一检索接口设计

**Decision**: adapter.py 提供 `search(query)` 方法，内部并行调用 dynamic.search() 和 files.search()，合并结果后按来源类型分组返回。

**返回结构**:
```python
@dataclass
class MemorySearchResult:
    source: str          # "dynamic" / "files"
    content: str
    score: float         # 1.0 for files, 0.0~1.0 for dynamic
    metadata: dict
```

**Rationale**:
- 两层记忆的检索方式不同（语义 vs 关键词），统一接口屏蔽差异
- 文件记忆的关键词匹配给 score=1.0（确定性匹配）
- 动态记忆的语义匹配给 0.0~1.0 的实际评分

**Alternatives considered**:
- 统一评分：两层用相同评分标准不现实，语义和精确匹配的语义不同
- 仅动态记忆搜索：文件记忆是重要的项目知识，不能忽略
