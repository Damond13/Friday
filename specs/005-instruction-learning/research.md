# Research: 指令学习模块技术决策

**Date**: 2026-06-02 | **Branch**: `005-instruction-learning`

## R001: YAML 指令文件格式设计

**Decision**: 每条指令一个 YAML 文件，使用固定的 schema 结构。

**Rationale**:
- 单文件=单指令，便于人工编辑和 Git 管理
- YAML 天然人可读，符合 Constitution III（本地优先）
- 已有 PyYAML 依赖（config.py 使用），无新依赖引入

**Schema 设计**:

```yaml
# ~/.friday/instructions/deploy.yaml
name: deploy
trigger: "deploy"
type: single  # single / workflow / conditional
description: "部署项目"
actions:
  - command: "./deploy.sh"
    description: "执行部署脚本"
    confirm: false
created_at: "2026-06-02T10:00:00"
updated_at: "2026-06-02T10:00:00"
```

**Alternatives considered**:
- SQLite 存储：结构化好查询快，但不便于人工直接编辑（违反 Constitution V 简洁实用）
- JSON 存储：机器友好但人可读性不如 YAML
- 单一大文件存所有指令：编辑冲突风险高，不符合 Constitution III 人工可控原则

## R002: 匹配算法选择

**Decision**: 两级匹配策略 — 精确匹配 + 关键词词频（TF）匹配。

**Rationale**:
- 精确匹配（trigger 字段完全包含在输入中）：100% 准确，零误判
- 关键词 TF 匹配（输入文本与 trigger/keywords 分词后计算重叠度）：处理模糊场景
- 不使用向量检索：向量检索由 knowledge 模块负责，instruction 保持轻量
- 纯 Python 实现，无额外依赖

**算法细节**:
1. 对输入文本分词（按空格和标点切分）
2. 精确匹配：trigger 完全出现在分词结果中 → 评分 1.0
3. 关键词匹配：计算 trigger 分词与输入分词的 Jaccard 相似度 → 评分 0~1.0
4. 阈值：仅返回评分 ≥ 0.3 的结果，按评分降序排列

**Alternatives considered**:
- ChromaDB 向量检索：需要 embedding 依赖，过于重量级
- 正则匹配：灵活性不足，难以处理中文分词
- 编辑距离：计算量大，对长文本效果差

## R003: 文件命名规范

**Decision**: 使用 trigger 的 slug 化作为文件名（小写 + 连字符）。

**Rationale**:
- 文件名即指令名，直观对应
- slug 化处理中英文：中文用拼音或 hash，英文用小写连字符
- 同名覆盖：同一 trigger 名只允许一个文件

**规则**:
- 英文 trigger: `deploy` → `deploy.yaml`
- 带空格 trigger: `check disk` → `check-disk.yaml`
- 中文 trigger: `部署` → 对 trigger 做 slug 化，优先使用 description 中的英文名

**Alternatives considered**:
- UUID 文件名：不直观，无法通过文件名识别指令
- 使用 name 字段而非 trigger：name 可能包含特殊字符
