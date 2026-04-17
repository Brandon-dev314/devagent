from app.agent.router import IntentRouter, Intent


class TestIntentRouter:
    def setup_method(self):
        self.router = IntentRouter()

    def test_how_to_question_is_docs(self):
        assert self.router.classify("How do I configure CORS?") == Intent.DOCS_QUERY

    def test_what_is_question_is_docs(self):
        assert self.router.classify("What is dependency injection?") == Intent.DOCS_QUERY

    def test_explain_is_docs(self):
        assert self.router.classify("Explain middleware in FastAPI") == Intent.DOCS_QUERY

    def test_question_mark_is_docs(self):
        assert self.router.classify("FastAPI path parameters?") == Intent.DOCS_QUERY

    def test_docs_keyword_is_docs(self):
        assert self.router.classify("Show me the documentation for routing") == Intent.DOCS_QUERY

    def test_create_issue_is_github(self):
        assert self.router.classify("Create an issue for the login bug") == Intent.GITHUB_ACTION

    def test_open_issue_is_github(self):
        assert self.router.classify("Open a bug ticket for the API timeout") == Intent.GITHUB_ACTION

    def test_list_prs_is_github(self):
        assert self.router.classify("List open pull requests") == Intent.GITHUB_ACTION

    def test_github_keyword_is_github(self):
        assert self.router.classify("Check github for related issues") == Intent.GITHUB_ACTION

    def test_run_code_is_code_exec(self):
        assert self.router.classify("Run this code: print('hello')") == Intent.CODE_EXEC

    def test_code_block_is_code_exec(self):
        assert self.router.classify("Execute ```python\nprint('hi')```") == Intent.CODE_EXEC

    def test_execute_is_code_exec(self):
        assert self.router.classify("Execute this Python script") == Intent.CODE_EXEC

    def test_sql_is_db_query(self):
        assert self.router.classify("SELECT * FROM users WHERE active = true") == Intent.DB_QUERY

    def test_query_database_is_db(self):
        assert self.router.classify("Query the database for active users") == Intent.DB_QUERY

    def test_show_from_table_is_db(self):
        assert self.router.classify("Show all records from the orders table") == Intent.DB_QUERY

    def test_greeting_is_general(self):
        assert self.router.classify("Hello!") == Intent.GENERAL

    def test_thanks_is_general(self):
        assert self.router.classify("Thanks, that was helpful") == Intent.GENERAL

    def test_create_issue_about_docs_is_github(self):
        result = self.router.classify("Create an issue about the documentation")
        assert result == Intent.GITHUB_ACTION
    def test_docs_needs_rag_tool(self):
        tools = self.router.get_required_tools(Intent.DOCS_QUERY)
        assert "rag" in tools

    def test_github_needs_github_tool(self):
        tools = self.router.get_required_tools(Intent.GITHUB_ACTION)
        assert "github" in tools

    def test_general_needs_no_tools(self):
        tools = self.router.get_required_tools(Intent.GENERAL)
        assert len(tools) == 0