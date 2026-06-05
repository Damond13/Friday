"""交互模式 REPL 循环"""

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from friday.cli import session as session_mod
from friday.cli import slash
from friday.cli.display import (
    console,
    show_assistant_separator,
    show_config_guide,
    show_welcome,
    show_error,
    show_tool_call,
    show_tool_result,
)
from friday.cli.session import Session
from friday.llm import LLMError
from friday.llm.prompts import PromptContext


def _process_input(user_input: str, session: Session) -> bool:
    """处理用户输入，返回 True 表示应退出 REPL"""
    stripped = user_input.strip()
    if not stripped:
        return False
    result = slash.dispatch(stripped, session)
    if result is not None:
        if result.should_exit:
            session_mod.save_session(session)
            return True
        return False
    if _try_quick_note(stripped):
        return False
    session.add_message("user", stripped)
    try:
        _agent_reply(session)
    except LLMError as e:
        show_error(str(e))
        session.messages.pop()
    return False


def _try_quick_note(text: str) -> bool:
    """识别"记一下 xxx"意图，自动录入知识库"""
    prefixes = ("记一下", "记录一下", "记一下：", "记一下:")
    for p in prefixes:
        if text.startswith(p):
            content = text[len(p):].strip()
            if content:
                from friday.knowledge.adapter import add_note
                from friday.cli.display import console
                note = add_note(title=content[:50], content=content)
                console.print(f"[green]✓[/green] 已记录笔记 (id: {note.id})")
                return True
    return False


def run_repl() -> None:
    """启动交互模式 REPL"""
    from friday.config import get_llm_config
    try:
        get_llm_config()
    except ValueError:
        show_config_guide()
        return
    current_session = session_mod.create_session()
    _setup_safety_callbacks()
    show_welcome()
    from friday.knowledge.watcher import start_watcher, stop_watcher
    start_watcher()
    prompt = PromptSession(
        "Friday> ", history=FileHistory(str(session_mod.SESSIONS_DIR.parent / "history")),
    )
    ctrl_c_count = 0
    try:
        while True:
            try:
                user_input = prompt.prompt()
                ctrl_c_count = 0
            except KeyboardInterrupt:
                ctrl_c_count += 1
                if ctrl_c_count >= 2:
                    console.print("\n[dim]再见！[/dim]")
                    break
                console.print("\n[dim]（再按一次 Ctrl+C 退出）[/dim]")
                continue
            except EOFError:
                console.print("\n[dim]再见！[/dim]")
                break
            if _process_input(user_input, current_session):
                break
    finally:
        stop_watcher()


def _agent_reply(session: Session) -> None:
    """通过 Agent 循环调用 LLM，支持工具调用"""
    from friday.llm.agent import run_agent_loop
    show_assistant_separator()
    messages = session.to_messages()
    context = _build_context(session)
    result = run_agent_loop(
        messages,
        context=context,
        on_tool_call=show_tool_call,
        on_tool_result=show_tool_result,
    )
    if result.reply:
        console.print(result.reply)
    console.print()
    console.print()
    if result.reply:
        session.add_message("assistant", result.reply)


def _build_context(session: Session) -> PromptContext:
    """组装 Prompt 上下文：从记忆系统加载用户偏好"""
    memories: list[str] = []
    try:
        import io, sys
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            from friday.memory.dynamic import search_memory
            results = search_memory("用户偏好 习惯 设置", limit=5)
            memories = [r["memory"] for r in results if "memory" in r]
        finally:
            sys.stderr = old_stderr
    except Exception:
        pass
    return PromptContext(user_memories=memories)


def _setup_safety_callbacks() -> None:
    """注册安全确认回调"""
    from rich.prompt import Confirm
    from friday.executor import set_confirm_callback, SafetyLevel
    from friday.llm.executors import set_confirm_callback as set_llm_confirm

    def _confirm_command(command: str, level: SafetyLevel) -> bool:
        label = "危险" if level == SafetyLevel.DANGEROUS else "需确认"
        return Confirm.ask(f"[{label}] 执行: {command}", default=False)

    def _confirm_overwrite(desc: str) -> bool:
        return Confirm.ask(f"[需确认] {desc}", default=False)

    set_confirm_callback(_confirm_command)
    set_llm_confirm(_confirm_overwrite)
