"""
Tools package — Herramientas disponibles para el agente.
"""

from app.tools.base import BaseTool, ToolResult
from app.tools.github_tool import GitHubCreateIssueTool, GitHubSearchIssuesTool
from app.tools.database_tool import DatabaseQueryTool
from app.tools.code_executor import CodeExecutorTool

TOOL_REGISTRY: dict[str, BaseTool] = {
    "create_issue": GitHubCreateIssueTool(),
    "search_issues": GitHubSearchIssuesTool(),
    "query_db": DatabaseQueryTool(),
    "exec_code": CodeExecutorTool(),
}


def get_tool(name: str) -> BaseTool | None:
    return TOOL_REGISTRY.get(name)


def get_all_tools() -> list[BaseTool]:
    return list(TOOL_REGISTRY.values())


def get_openai_tools_schema() -> list[dict]:
    return [tool.to_openai_schema() for tool in TOOL_REGISTRY.values()]