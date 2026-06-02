"""输出处理 — 短输出原样返回，长输出截断"""

MAX_LINES = 20
TRUNCATE_MARKER = "\n... (输出已截断，共 {total} 行)"


def format_output(stdout: str) -> str:
    """格式化标准输出，超长时截断"""
    lines = stdout.rstrip("\n").split("\n")
    if len(lines) <= MAX_LINES:
        return stdout
    kept = "\n".join(lines[:MAX_LINES])
    return kept + TRUNCATE_MARKER.format(total=len(lines)) + "\n"


def summarize_output(stdout: str) -> str:
    """使用 LLM 摘要长输出（预留接口，MVP 用截断代替）"""
    return format_output(stdout)


def format_error(exit_code: int | None, stderr: str) -> str:
    """格式化错误输出为用户友好的消息"""
    if exit_code is None:
        return stderr or "命令执行异常"

    error_map = {
        126: "权限不足，无法执行该命令",
        127: "命令未找到，请检查命令拼写",
    }

    friendly = error_map.get(exit_code, "")
    if friendly and not stderr.strip():
        return friendly

    if friendly:
        return f"{friendly}\n{stderr.strip()}"

    return stderr.strip() or f"命令执行失败 (退出码: {exit_code})"
