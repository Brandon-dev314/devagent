from app.tools.base import BaseTool, ToolParameter, ToolResult
from app.tools import get_tool, get_all_tools, get_openai_tools_schema, TOOL_REGISTRY


class TestToolResult:
    def test_success_result(self):
        result = ToolResult(success=True, output="Done!")
        assert result.success
        assert result.output == "Done!"
        assert result.error == ""

    def test_error_result(self):
        result = ToolResult(success=False, output="", error="Something went wrong")
        assert not result.success
        assert result.error == "Something went wrong"

    def test_result_with_metadata(self):
        result = ToolResult(
            success=True,
            output="Issue created",
            metadata={"issue_number": 42},
        )
        assert result.metadata["issue_number"] == 42


class TestToolRegistry:

    def test_registry_has_tools(self):
        assert len(TOOL_REGISTRY) > 0

    def test_get_existing_tool(self):
        tool = get_tool("exec_code")
        assert tool is not None
        assert tool.name == "exec_code"

    def test_get_nonexistent_tool(self):
        assert get_tool("nonexistent_tool") is None

    def test_get_all_tools(self):
        tools = get_all_tools()
        assert len(tools) == len(TOOL_REGISTRY)

    def test_all_tools_have_names(self):
        for tool in get_all_tools():
            assert tool.name
            assert len(tool.name) > 0

    def test_all_tools_have_descriptions(self):
        for tool in get_all_tools():
            assert tool.description
            assert len(tool.description) > 10

    def test_tool_names_are_unique(self):
        names = [tool.name for tool in get_all_tools()]
        assert len(names) == len(set(names))


class TestOpenAISchema:

    def test_schema_has_correct_structure(self):
        schemas = get_openai_tools_schema()
        assert len(schemas) > 0

        for schema in schemas:
            assert schema["type"] == "function"
            assert "function" in schema
            assert "name" in schema["function"]
            assert "description" in schema["function"]
            assert "parameters" in schema["function"]

    def test_schema_parameters_have_properties(self):
        schemas = get_openai_tools_schema()

        for schema in schemas:
            params = schema["function"]["parameters"]
            assert params["type"] == "object"
            assert "properties" in params

    def test_exec_code_schema(self):
        tool = get_tool("exec_code")
        assert tool is not None

        schema = tool.to_openai_schema()
        props = schema["function"]["parameters"]["properties"]

        assert "code" in props
        assert props["code"]["type"] == "string"


class TestParameterValidation:
    def test_validate_with_required_params(self):
        tool = get_tool("exec_code")
        assert tool is not None

        is_valid, error = tool.validate_params(code="print('hi')")
        assert is_valid
        assert error == ""

    def test_validate_missing_required_param(self):
        tool = get_tool("create_issue")
        assert tool is not None

        is_valid, error = tool.validate_params(title="Bug report")
        assert not is_valid
        assert "repo" in error