"""Friday CLI 入口 — 交互模式 + 单次执行"""

import typer
from rich.console import Console

from friday.cli.display import show_config_guide, show_error

app = typer.Typer(help="Friday — 你的专属 AI 搭档", add_completion=False)
console = Console()


def check_llm_config() -> bool:
    """检查 LLM 配置，未配置时显示引导并返回 False"""
    from friday.config import get_llm_config
    try:
        get_llm_config()
        return True
    except ValueError:
        show_config_guide()
        return False


def run_single(message: str) -> None:
    """单次执行模式：输出回复后退出"""
    if not check_llm_config():
        raise SystemExit(1)
    from friday.llm import chat, LLMError
    messages = [{"role": "user", "content": message}]
    try:
        response = chat(messages)
        console.print(response.content)
    except LLMError as e:
        show_error(str(e))
        raise SystemExit(1) from e


def run_interactive() -> None:
    """交互模式"""
    from friday.cli.repl import run_repl
    run_repl()


@app.command()
def main(
    message: str = typer.Argument(None, help="直接提问（不进入交互模式）"),
) -> None:
    """Friday — 你的专属 AI 搭档"""
    if message is not None:
        run_single(message)
    else:
        run_interactive()


if __name__ == "__main__":
    app()
