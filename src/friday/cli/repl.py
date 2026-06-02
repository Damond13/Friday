"""交互模式 REPL 循环"""

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from friday.cli import session as session_mod
from friday.cli import slash
from friday.cli.display import (
    console,
    show_assistant_separator,
    show_config_guide,
    show_streaming_token,
    show_welcome,
    show_error,
)
from friday.cli.session import Session
from friday.llm import chat_stream, LLMError


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
        _stream_reply(session)
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


def _stream_reply(session: Session) -> None:
    """流式调用 LLM 并输出回复"""
    show_assistant_separator()
    messages = session.to_messages()
    full_reply = ""
    try:
        for token in chat_stream(messages):
            show_streaming_token(token)
            full_reply += token
    except KeyboardInterrupt:
        console.print("\n[dim]（回复已中断）[/dim]")
    console.print()
    console.print()
    if full_reply:
        session.add_message("assistant", full_reply)
