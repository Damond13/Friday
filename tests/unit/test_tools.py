"""tools.py 单元测试"""

from friday.llm.tools import (
    get_tool_definitions, SHELL_EXECUTE, FILE_READ, FILE_WRITE,
    KNOWLEDGE_SEARCH, KNOWLEDGE_ADD, INSTRUCTION_ADD, INSTRUCTION_SEARCH,
    INSTRUCTION_LIST, INSTRUCTION_DELETE,
)


def test_get_tool_definitions_returns_list():
    tools = get_tool_definitions()
    assert isinstance(tools, list)
    assert len(tools) == 9


def test_tool_schema_format():
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
    tools = get_tool_definitions()
    names = {t["function"]["name"] for t in tools}
    assert names == {
        "shell_execute", "file_read", "file_write",
        "knowledge_search", "knowledge_add",
        "instruction_add", "instruction_search",
        "instruction_list", "instruction_delete",
    }


def test_shell_execute_requires_command():
    schema = SHELL_EXECUTE.to_openai_format()
    params = schema["function"]["parameters"]
    assert "command" in params["required"]
    assert "command" in params["properties"]


def test_file_write_requires_path_and_content():
    schema = FILE_WRITE.to_openai_format()
    params = schema["function"]["parameters"]
    assert set(params["required"]) == {"path", "content"}


def test_knowledge_search_defaults():
    schema = KNOWLEDGE_SEARCH.to_openai_format()
    props = schema["function"]["parameters"]["properties"]
    assert props["limit"]["default"] == 5


def test_knowledge_add_requires_title_and_content():
    schema = KNOWLEDGE_ADD.to_openai_format()
    params = schema["function"]["parameters"]
    assert set(params["required"]) == {"title", "content"}


def test_knowledge_add_has_optional_tags():
    schema = KNOWLEDGE_ADD.to_openai_format()
    params = schema["function"]["parameters"]
    assert "tags" not in params["required"]
    assert "tags" in params["properties"]


def test_instruction_add_requires_trigger_and_actions():
    schema = INSTRUCTION_ADD.to_openai_format()
    params = schema["function"]["parameters"]
    assert set(params["required"]) == {"trigger", "actions"}


def test_instruction_search_defaults():
    schema = INSTRUCTION_SEARCH.to_openai_format()
    props = schema["function"]["parameters"]["properties"]
    assert props["limit"]["default"] == 5


def test_instruction_delete_requires_name():
    schema = INSTRUCTION_DELETE.to_openai_format()
    params = schema["function"]["parameters"]
    assert params["required"] == ["name"]
