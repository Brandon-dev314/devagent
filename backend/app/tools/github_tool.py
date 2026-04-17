import logging
import httpx

from app.config import settings
from app.tools.base import BaseTool, ToolParameter, ToolResult

logger = logging.getLogger("devagent.tools.github")

GITHUB_API_URL = "https://api.github.com"


class GitHubCreateIssueTool(BaseTool):
    @property
    def name(self) -> str:
        return "create_issue"

    @property
    def description(self) -> str:
        return (
            "Create a new issue in a GitHub repository. "
            "Use this when the user wants to report a bug, "
            "request a feature, or create a task."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="repo",
                type="string",
                description="Repository in 'owner/repo' format (e.g., 'octocat/hello-world')",
            ),
            ToolParameter(
                name="title",
                type="string",
                description="Issue title — clear and descriptive",
            ),
            ToolParameter(
                name="body",
                type="string",
                description="Issue body with details, steps to reproduce, etc.",
                required=False,
                default="",
            ),
            ToolParameter(
                name="labels",
                type="array",
                description="Labels to apply (e.g., ['bug', 'high-priority'])",
                required=False,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        is_valid, error = self.validate_params(**kwargs)
        if not is_valid:
            return ToolResult(success=False, output="", error=error)

        repo = kwargs["repo"]
        title = kwargs["title"]
        body = kwargs.get("body", "")
        labels = kwargs.get("labels", [])

        if not settings.github_token:
            return ToolResult(
                success=False,
                output="",
                error="GitHub token not configured. Set GITHUB_TOKEN in .env",
            )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{GITHUB_API_URL}/repos/{repo}/issues",
                    headers={
                        "Authorization": f"token {settings.github_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    json={
                        "title": title,
                        "body": body,
                        "labels": labels,
                    },
                    timeout=30.0,
                )

                if response.status_code == 201:
                    data = response.json()
                    issue_url = data.get("html_url", "")
                    issue_number = data.get("number", 0)

                    logger.info("✅ Issue #%d created: %s", issue_number, issue_url)

                    return ToolResult(
                        success=True,
                        output=f"Issue #{issue_number} created successfully: {issue_url}",
                        metadata={
                            "issue_number": issue_number,
                            "url": issue_url,
                        },
                    )
                else:
                    error_msg = response.json().get("message", response.text)
                    logger.error("❌ GitHub API error: %s", error_msg)
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"GitHub API error ({response.status_code}): {error_msg}",
                    )

            except httpx.TimeoutException:
                return ToolResult(
                    success=False,
                    output="",
                    error="GitHub API request timed out",
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unexpected error: {str(e)}",
                )


class GitHubSearchIssuesTool(BaseTool):
    @property
    def name(self) -> str:
        return "search_issues"

    @property
    def description(self) -> str:
        return (
            "Search for existing issues in a GitHub repository. "
            "Use this to find related bugs, check if an issue already exists, "
            "or list open issues."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="repo",
                type="string",
                description="Repository in 'owner/repo' format",
            ),
            ToolParameter(
                name="query",
                type="string",
                description="Search keywords",
                required=False,
                default="",
            ),
            ToolParameter(
                name="state",
                type="string",
                description="Filter by state",
                required=False,
                default="open",
                enum=["open", "closed", "all"],
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        repo = kwargs.get("repo", "")
        query = kwargs.get("query", "")
        state = kwargs.get("state", "open")

        if not settings.github_token:
            return ToolResult(
                success=False,
                output="",
                error="GitHub token not configured. Set GITHUB_TOKEN in .env",
            )

        async with httpx.AsyncClient() as client:
            try:
                if query:
                    search_query = f"{query} repo:{repo} is:issue state:{state}"
                    response = await client.get(
                        f"{GITHUB_API_URL}/search/issues",
                        headers={
                            "Authorization": f"token {settings.github_token}",
                            "Accept": "application/vnd.github.v3+json",
                        },
                        params={"q": search_query, "per_page": 10},
                        timeout=30.0,
                    )
                else:
                    response = await client.get(
                        f"{GITHUB_API_URL}/repos/{repo}/issues",
                        headers={
                            "Authorization": f"token {settings.github_token}",
                            "Accept": "application/vnd.github.v3+json",
                        },
                        params={"state": state, "per_page": 10},
                        timeout=30.0,
                    )

                if response.status_code == 200:
                    data = response.json()

                    issues = data.get("items", data) if isinstance(data, dict) else data

                    if not issues:
                        return ToolResult(
                            success=True,
                            output=f"No issues found in {repo} matching '{query}'.",
                        )

                    # Formatear resultados
                    lines = [f"Found {len(issues)} issue(s) in {repo}:\n"]
                    for issue in issues[:10]:  # Máximo 10
                        number = issue.get("number", "?")
                        title = issue.get("title", "Untitled")
                        issue_state = issue.get("state", "unknown")
                        url = issue.get("html_url", "")
                        lines.append(f"  #{number} [{issue_state}] {title}")
                        lines.append(f"    {url}")

                    output = "\n".join(lines)
                    logger.info("🔍 Found %d issues in %s", len(issues), repo)

                    return ToolResult(
                        success=True,
                        output=output,
                        metadata={"count": len(issues)},
                    )
                else:
                    error_msg = response.json().get("message", response.text)
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"GitHub API error ({response.status_code}): {error_msg}",
                    )

            except httpx.TimeoutException:
                return ToolResult(
                    success=False, output="", error="GitHub API request timed out",
                )
            except Exception as e:
                return ToolResult(
                    success=False, output="", error=f"Unexpected error: {str(e)}",
                )