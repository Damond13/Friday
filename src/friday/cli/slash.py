"""斜杠命令注册与分发"""

from collections.abc import Callable
from dataclasses import dataclass

from friday.cli.session import Session


@dataclass
class CommandResult:
    """命令执行结果"""

    should_exit: bool = False
    message: str = ""


CommandHandler = Callable[..., CommandResult]

# 命令注册表：name → (description, handler)
_COMMANDS: dict[str, tuple[str, CommandHandler]] = {}


def _register(name: str, description: str) -> Callable[[CommandHandler], CommandHandler]:
    """装饰器：注册斜杠命令"""
    def decorator(func: CommandHandler) -> CommandHandler:
        _COMMANDS[name] = (description, func)
        return func
    return decorator


def get_commands() -> dict[str, tuple[str, CommandHandler]]:
    """获取所有已注册命令"""
    return _COMMANDS.copy()


@_register("help", "显示所有可用命令")
def cmd_help(session: Session, args: str = "") -> CommandResult:
    from friday.cli.display import console
    from rich.table import Table
    table = Table(show_header=True, header_style="bold")
    table.add_column("命令", width=15)
    table.add_column("说明")
    table.add_row("/help", "显示所有可用命令")
    table.add_row("/save", "保存当前会话")
    table.add_row("/history", "列出历史会话")
    table.add_row("/load <编号>", "恢复历史会话")
    table.add_row("/exit, /quit", "退出交互模式")
    console.print(table)
    return CommandResult()


@_register("exit", "退出交互模式")
def cmd_exit(session: Session, args: str = "") -> CommandResult:
    from friday.cli.display import console
    console.print("[dim]再见！[/dim]")
    return CommandResult(should_exit=True)


@_register("quit", "退出交互模式")
def cmd_quit(session: Session, args: str = "") -> CommandResult:
    return cmd_exit(session)


@_register("save", "保存当前会话")
def cmd_save(session: Session, args: str = "") -> CommandResult:
    from friday.cli import session as session_mod
    from friday.cli.display import show_save_success
    path = session_mod.save_session(session)
    show_save_success(str(path))
    return CommandResult()


@_register("history", "列出历史会话")
def cmd_history(session: Session, args: str = "") -> CommandResult:
    from friday.cli import session as session_mod
    from friday.cli.display import show_history_list
    sessions = session_mod.list_sessions()
    show_history_list(sessions)
    return CommandResult()


@_register("load", "恢复历史会话")
def cmd_load(session: Session, args: str = "") -> CommandResult:
    from friday.cli import session as session_mod
    from friday.cli.display import console
    if not args.strip():
        console.print("[yellow]用法: /load <编号>[/yellow]")
        return CommandResult()
    try:
        idx = int(args.strip()) - 1
    except ValueError:
        console.print("[red]请输入有效的编号[/red]")
        return CommandResult()
    sessions = session_mod.list_sessions()
    if idx < 0 or idx >= len(sessions):
        console.print("[red]会话不存在[/red]")
        return CommandResult()
    try:
        loaded = session_mod.load_session(sessions[idx]["id"])
    except FileNotFoundError:
        console.print("[red]会话文件不存在[/red]")
        return CommandResult()
    session.id = loaded.id
    session.created_at = loaded.created_at
    session.messages = loaded.messages
    session.summary = loaded.summary
    console.print(f"[green]✓[/green] 已加载会话 ({len(session.messages)} 条消息)")
    return CommandResult()


def dispatch(user_input: str, session: Session) -> CommandResult | None:
    """分发斜杠命令，非斜杠输入返回 None"""
    if not user_input.startswith("/"):
        return None
    parts = user_input[1:].split(maxsplit=1)
    name = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    if name not in _COMMANDS:
        from friday.cli.display import console
        console.print(f"[yellow]未知命令: /{name}，输入 /help 查看可用命令[/yellow]")
        return CommandResult()
    _, handler = _COMMANDS[name]
    return handler(session, args=args)
