"""Rich 终端输出格式化"""

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from friday import __version__
from friday.config import CONFIG_PATH

console = Console()


def show_welcome() -> None:
    """显示欢迎信息"""
    console.print()
    console.print(Panel(f"Friday v{__version__} — 你的专属 AI 搭档", style="bold magenta"))
    console.print("输入 [bold]/help[/bold] 查看可用命令")
    console.print()


def show_error(message: str) -> None:
    """显示错误信息"""
    console.print(f"[bold red]错误:[/bold red] {message}")


def show_config_guide() -> None:
    """显示 API Key 配置引导"""
    console.print(f"[bold yellow]LLM 未配置[/bold yellow]")
    console.print(f"请编辑 [bold]{CONFIG_PATH}[/bold] 添加 API Key：")
    console.print()
    console.print("[dim]llm:\n  provider: zhipu\n  providers:\n    zhipu:\n      api_key: your-key-here\n      model: glm-4-flash[/dim]")
    console.print()


def show_save_success(path: str) -> None:
    """显示保存成功提示"""
    console.print(f"[green]✓[/green] 会话已保存到 {path}")


def show_history_list(sessions: list[dict]) -> None:
    """显示历史会话列表"""
    if not sessions:
        console.print("[dim]暂无保存的会话[/dim]")
        return
    table = Table(show_header=True, header_style="bold")
    table.add_column("编号", width=6)
    table.add_column("时间", width=20)
    table.add_column("摘要")
    for i, s in enumerate(sessions, 1):
        table.add_row(str(i), s.get("created_at", ""), s.get("summary", ""))
    console.print(table)


def show_streaming_token(token: str) -> None:
    """输出单个流式 token"""
    console.print(token, end="")


def show_search_results(results: list) -> None:
    """显示知识库检索结果"""
    for i, r in enumerate(results, 1):
        source_tag = f"[dim][{r.source}][/dim]" if r.source else ""
        console.print(f"  [bold]#{i}[/bold] {r.title} {source_tag}")
        console.print(f"      {r.snippet}")
        if r.file_path:
            console.print(f"      [dim]{r.file_path}[/dim]")
        console.print()


def show_assistant_separator() -> None:
    """显示助手回复前的分隔线"""
    console.print(Rule(style="dim"))


def show_assistant_reply(reply: str) -> None:
    """显示助手回复内容（带 Friday: 前缀）"""
    console.print("[bold cyan]Friday:[/bold cyan] ", end="")
    console.print(reply)


def show_tool_call(name: str, arguments: dict) -> None:
    """显示正在执行的工具调用"""
    args_str = " ".join(f"{k}={v!r}" for k, v in arguments.items())
    console.print(f"  [bold yellow]🔧 {name}[/bold yellow] [dim]{args_str}[/dim]")


def show_tool_result(success: bool, output: str) -> None:
    """显示工具执行结果摘要"""
    icon = "[green]✓[/green]" if success else "[red]✗[/red]"
    preview = output[:200].replace("\n", " ")
    if len(output) > 200:
        preview += "..."
    console.print(f"  {icon} [dim]{preview}[/dim]")
