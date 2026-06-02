"""prompts.py 单元测试"""

from friday.llm.prompts import PromptContext, build_system_prompt


def test_build_system_prompt_no_context():
    """无 context 时只返回基础 prompt"""
    result = build_system_prompt()
    assert "Friday" in result
    assert "用户偏好" not in result


def test_build_system_prompt_empty_context():
    """空 context 时只返回基础 prompt"""
    ctx = PromptContext()
    result = build_system_prompt(ctx)
    assert "Friday" in result
    assert "用户偏好" not in result


def test_build_system_prompt_with_memories():
    """包含用户记忆"""
    ctx = PromptContext(user_memories=["喜欢简洁的回复", "偏好 Python"])
    result = build_system_prompt(ctx)
    assert "用户偏好与记忆" in result
    assert "喜欢简洁的回复" in result
    assert "偏好 Python" in result


def test_build_system_prompt_with_knowledge():
    """包含知识"""
    ctx = PromptContext(knowledge=["项目使用 SQLite 存储", "配置在 ~/.friday/"])
    result = build_system_prompt(ctx)
    assert "相关知识" in result
    assert "SQLite" in result


def test_build_system_prompt_with_instructions():
    """包含指令"""
    ctx = PromptContext(instructions=["每次启动先拉取最新代码"])
    result = build_system_prompt(ctx)
    assert "已学习的指令" in result
    assert "拉取最新代码" in result


def test_build_system_prompt_full_context():
    """完整 context"""
    ctx = PromptContext(
        user_memories=["喜欢深色主题"],
        knowledge=["使用 Typer 框架"],
        instructions=["提交前跑测试"],
    )
    result = build_system_prompt(ctx)
    assert "用户偏好与记忆" in result
    assert "相关知识" in result
    assert "已学习的指令" in result
