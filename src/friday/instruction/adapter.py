"""指令学习模块 — 统一接口"""

from datetime import datetime, timezone
from typing import Any

from friday.instruction.models import (
    Action,
    Instruction,
    InstructionType,
    MatchResult,
)
from friday.instruction import store, matcher

# 内存缓存
_cache: list[Instruction] | None = None


def _get_all() -> list[Instruction]:
    """获取全部指令（带缓存）"""
    global _cache
    if _cache is None:
        _cache = store.load_all()
    return _cache


def _invalidate_cache() -> None:
    """清除缓存"""
    global _cache
    _cache = None


def teach(
    name: str,
    trigger: str,
    actions: list[dict[str, Any]],
    type: str = "single",
    description: str = "",
    keywords: list[str] | None = None,
) -> Instruction:
    """创建一条新指令并保存到 YAML 文件"""
    _validate_trigger(trigger)
    _validate_actions(actions)

    # 多步工作流自动推断
    resolved_type = _resolve_type(type, actions, description)

    now = datetime.now(timezone.utc).isoformat()
    instr = Instruction(
        name=name,
        trigger=trigger,
        actions=[Action.from_dict(a) for a in actions],
        type=resolved_type,
        description=description,
        keywords=keywords or [],
        created_at=now,
        updated_at=now,
    )

    store.save(instr)
    _index_instruction(instr)
    _invalidate_cache()
    return instr


def match(text: str, top_k: int = 5) -> list[MatchResult]:
    """通过语义检索匹配用户输入文本到已知指令"""
    from friday.knowledge.adapter import search_instructions
    results = search_instructions(text, limit=top_k)
    instructions = _get_all()
    matched: list[MatchResult] = []
    for sr in results:
        for instr in instructions:
            if instr.name == sr.title or instr.trigger == sr.title:
                matched.append(MatchResult(
                    instruction=instr, score=sr.score, match_type="semantic",
                ))
                break
    return matched[:top_k]


def list_instructions() -> list[Instruction]:
    """列出所有已保存的指令，按名称排序"""
    instructions = _get_all()
    return sorted(instructions, key=lambda i: i.name)


def remove(name: str) -> bool:
    """删除指定名称的指令"""
    from friday.knowledge.adapter import delete_instruction_index
    instructions = _get_all()
    for instr in instructions:
        if instr.name == name:
            slug = store.slugify(instr.trigger)
            deleted = store.delete(slug)
            if deleted:
                try:
                    delete_instruction_index(f"instr_{slug}")
                except Exception:
                    pass
                _invalidate_cache()
            return deleted
    return False


def reload() -> int:
    """重新从文件系统加载所有指令文件"""
    _invalidate_cache()
    return len(_get_all())


def _validate_trigger(trigger: str) -> None:
    """验证触发词"""
    if not trigger or len(trigger.strip()) < 2:
        raise ValueError("触发词不能为空且长度不能少于 2 个字符")


def _validate_actions(actions: list[dict[str, Any]]) -> None:
    """验证动作列表"""
    if not actions:
        raise ValueError("动作列表不能为空")
    for i, action in enumerate(actions):
        if not action.get("command"):
            raise ValueError(f"第 {i + 1} 个动作缺少 command 字段")


def _resolve_type(
    type_str: str,
    actions: list[dict[str, Any]],
    description: str,
) -> InstructionType:
    """推断指令类型：多步自动识别为 workflow"""
    if type_str == "conditional" and not description:
        raise ValueError("条件分支指令必须提供 description 描述")
    if type_str != "single":
        return InstructionType(type_str)
    # 未显式指定且多步 → 自动推断为 workflow
    if len(actions) > 1:
        return InstructionType.WORKFLOW
    return InstructionType.SINGLE


def search_instructions(query: str, limit: int = 5) -> list[dict]:
    """语义检索指令，返回 [{name, trigger, score, snippet}]"""
    from friday.knowledge.adapter import search_instructions as kb_search
    results = kb_search(query, limit=limit)
    return [
        {"name": r.title, "trigger": r.title,
         "score": r.score, "snippet": r.snippet}
        for r in results
    ]


def _index_instruction(instr: Instruction) -> None:
    """为指令建立 FTS + 向量索引"""
    from friday.knowledge.adapter import index_instruction
    slug = store.slugify(instr.trigger)
    path = str(store.INSTRUCTIONS_DIR / f"{slug}.yaml")
    keywords = instr.keywords + [instr.trigger]
    index_instruction(
        instr_id=f"instr_{slug}",
        trigger=instr.trigger,
        content=instr.description or instr.trigger,
        keywords=keywords,
        file_path=path,
    )
