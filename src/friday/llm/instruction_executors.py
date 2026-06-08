"""指令管理执行器 — instruction_add/search/list/delete"""

from friday.llm.types import ToolResult


async def exec_instruction_add(arguments: dict) -> ToolResult:
    """教会一条新指令"""
    trigger = arguments.get("trigger", "").strip()
    actions = arguments.get("actions", [])
    name = arguments.get("name") or trigger
    keywords = arguments.get("keywords") or []
    if not trigger:
        return ToolResult(tool_call_id="", success=False, output="缺少 trigger 参数")
    if not actions:
        return ToolResult(tool_call_id="", success=False, output="缺少 actions 参数")
    try:
        from friday.instruction.adapter import teach
        instr = teach(
            name=name, trigger=trigger, actions=actions,
            keywords=keywords, description=f"触发词: {trigger}",
        )
        return ToolResult(
            tool_call_id="", success=True,
            output=f"已学会指令「{instr.name}」（触发词: {instr.trigger}）",
        )
    except Exception as e:
        return ToolResult(tool_call_id="", success=False, output=f"学习失败: {e}")


async def exec_instruction_search(arguments: dict) -> ToolResult:
    """语义检索已学指令"""
    query = arguments.get("query", "")
    limit = arguments.get("limit", 5)
    if not query:
        return ToolResult(tool_call_id="", success=False, output="缺少 query 参数")
    try:
        from friday.instruction.adapter import search_instructions
        results = search_instructions(query, limit=limit)
        if not results:
            return ToolResult(tool_call_id="", success=True, output="未找到匹配指令")
        parts: list[str] = []
        for r in results:
            parts.append(f"- {r['name']}（匹配度: {r['score']:.2f}）")
        return ToolResult(tool_call_id="", success=True, output="\n".join(parts))
    except Exception as e:
        return ToolResult(tool_call_id="", success=False, output=f"检索失败: {e}")


async def exec_instruction_list(arguments: dict) -> ToolResult:
    """列出所有已学指令"""
    try:
        from friday.instruction.adapter import list_instructions
        instructions = list_instructions()
        if not instructions:
            return ToolResult(tool_call_id="", success=True, output="还没有学会任何指令")
        parts: list[str] = []
        for instr in instructions:
            actions_desc = ", ".join(a.command for a in instr.actions)
            parts.append(f"- {instr.name}（触发词: {instr.trigger}，动作: {actions_desc}）")
        return ToolResult(tool_call_id="", success=True, output="\n".join(parts))
    except Exception as e:
        return ToolResult(tool_call_id="", success=False, output=f"列表失败: {e}")


async def exec_instruction_delete(arguments: dict) -> ToolResult:
    """删除一条已学指令"""
    name = arguments.get("name", "").strip()
    if not name:
        return ToolResult(tool_call_id="", success=False, output="缺少 name 参数")
    try:
        from friday.instruction.adapter import remove
        deleted = remove(name)
        if deleted:
            return ToolResult(tool_call_id="", success=True, output=f"已删除指令「{name}」")
        return ToolResult(tool_call_id="", success=False, output=f"未找到指令「{name}」")
    except Exception as e:
        return ToolResult(tool_call_id="", success=False, output=f"删除失败: {e}")
