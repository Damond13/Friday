"""tools.py 单元测试"""

from friday.llm.tools import get_tool_definitions, SHELL_EXECUTE, FILE_READ, FILE_WRITE, KNOWLEDGE_SEARCH


def test_get_tool_definitions_returns_list():
    """应返回工具定义列表"""
    tools = get_tool_definitions()
    assert isinstance(tools, list)
    assert len(tools) == 4


def test_tool_schema_format():
    """每个工具定义应符合 OpenAI function calling 格式"""
    tools = get_tool_definitions()
    for tool in tools:
        assert tool["type"] == "function"
        assert "function" in tool
        func = tool["function"]
        assert "name" in func
        assert "description" in func
        assert "parameters" in func
        params = func["parameters"]
        assert params["type"] == "object"
        assert "properties" in params


def test_tool_names():
    """应包含所有预期的工具名称"""
    tools = get_tool_definitions()
    names = {t["function"]["name"] for t in tools}
    assert names == {"shell_execute", "file_read", "file_write", "knowledge_search"}


def test_shell_execute_requires_command():
    """shell_execute 必须有 command 参数"""
    schema = SHELL_EXECUTE.to_openai_format()
    params = schema["function"]["parameters"]
    assert "command" in params["required"]
    assert "command" in params["properties"]


def test_file_write_requires_path_and_content():
    """file_write 必须有 path 和 content"""
    schema = FILE_WRITE.to_openai_format()
    params = schema["function"]["parameters"]
    assert set(params["required"]) == {"path", "content"}


def test_knowledge_search_defaults():
    """knowledge_search 的 limit 应有默认值"""
    schema = KNOWLEDGE_SEARCH.to_openai_format()
    props = schema["function"]["parameters"]["properties"]
    assert props["limit"]["default"] == 5
