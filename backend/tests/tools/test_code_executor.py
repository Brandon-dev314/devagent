import pytest
from app.tools.code_executor import CodeExecutorTool
from app.tools.database_tool import DatabaseQueryTool


class TestCodeExecutor:
    def setup_method(self):
        self.tool = CodeExecutorTool()

    @pytest.mark.asyncio
    async def test_simple_print(self):
        result = await self.tool.execute(code="print('hello world')")
        assert result.success
        assert "hello world" in result.output

    @pytest.mark.asyncio
    async def test_math_expression(self):
        result = await self.tool.execute(code="print(2 + 2)")
        assert result.success
        assert "4" in result.output

    @pytest.mark.asyncio
    async def test_syntax_error(self):
        result = await self.tool.execute(code="print('hello'")
        assert not result.success
        assert "SyntaxError" in result.error

    @pytest.mark.asyncio
    async def test_runtime_error(self):
        result = await self.tool.execute(code="x = 1/0")
        assert not result.success
        assert "ZeroDivisionError" in result.error

    @pytest.mark.asyncio
    async def test_empty_code_rejected(self):
        result = await self.tool.execute(code="")
        assert not result.success

    @pytest.mark.asyncio
    async def test_unsupported_language(self):
        result = await self.tool.execute(code="console.log('hi')", language="javascript")
        assert not result.success
        assert "not supported" in result.error

    @pytest.mark.asyncio
    async def test_multiline_code(self):
        code = """
def greet(name):
    return f"Hello, {name}!"

print(greet("DevAgent"))
"""
        result = await self.tool.execute(code=code)
        assert result.success
        assert "Hello, DevAgent!" in result.output

    @pytest.mark.asyncio
    async def test_no_output(self):
        result = await self.tool.execute(code="x = 42")
        assert result.success
        assert "No output" in result.output


class TestDatabaseQueryValidation:
    def setup_method(self):
        self.tool = DatabaseQueryTool()

    def test_select_is_allowed(self):
        is_valid, error = self.tool._validate_query("SELECT * FROM users")
        assert is_valid

    def test_select_with_where_is_allowed(self):
        is_valid, error = self.tool._validate_query(
            "SELECT name, email FROM users WHERE active = true"
        )
        assert is_valid

    def test_cte_is_allowed(self):
        sql = "WITH active AS (SELECT * FROM users WHERE active = true) SELECT * FROM active"
        is_valid, error = self.tool._validate_query(sql)
        assert is_valid

    def test_insert_is_rejected(self):
        is_valid, error = self.tool._validate_query(
            "INSERT INTO users (name) VALUES ('hacker')"
        )
        assert not is_valid
        assert "INSERT" in error

    def test_update_is_rejected(self):
        is_valid, error = self.tool._validate_query(
            "UPDATE users SET admin = true"
        )
        assert not is_valid

    def test_delete_is_rejected(self):
        is_valid, error = self.tool._validate_query(
            "DELETE FROM users WHERE id = 1"
        )
        assert not is_valid

    def test_drop_is_rejected(self):
        is_valid, error = self.tool._validate_query("DROP TABLE users")
        assert not is_valid
        assert "DROP" in error

    def test_multiple_statements_rejected(self):
        is_valid, error = self.tool._validate_query(
            "SELECT 1; DROP TABLE users"
        )
        assert not is_valid

    def test_empty_query_handled(self):
        is_valid, error = self.tool._validate_query("SELECT 1")
        assert is_valid