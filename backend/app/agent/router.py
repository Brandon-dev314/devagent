import logging
import re
from enum import Enum

logger = logging.getLogger("devagent.router")


class Intent(str, Enum):
    DOCS_QUERY = "docs_query"
    GITHUB_ACTION = "github_action"
    CODE_EXEC = "code_exec"
    DB_QUERY = "db_query"
    GENERAL = "general"


class IntentRouter:

    GITHUB_PATTERNS = [
        r"\b(create|open|make|file|submit)\b.*\b(issue|bug|ticket|pr|pull request)\b",
        r"\b(issue|bug|ticket)\b.*\b(create|open|make|file)\b",
        r"\b(list|show|find|get)\b.*\b(issues|prs|pull requests|repos)\b",
        r"\bgithub\b",
    ]

    CODE_PATTERNS = [
        r"\b(run|execute|eval|try)\b.*\b(code|script|snippet|this)\b",
        r"```",  
        r"\b(what does this code do|explain this code)\b",
        r"\brunning?\b.*\b(python|javascript|bash|shell)\b",
    ]

    DB_PATTERNS = [
        r"\b(query|select|show|list|count|find)\b.*\b(from|in|database|db|table|users|records)\b",
        r"\bSELECT\b.*\bFROM\b",  
        r"\bdatabase\b",
    ]

    DOCS_PATTERNS = [
        r"\b(how|what|why|when|where|explain|tell me|describe)\b",
        r"\b(documentation|docs|reference|guide|tutorial|example)\b",
        r"\b(how to|how do|how can|what is|what are)\b",
        r"\?$",  
    ]

    def classify(self, message: str) -> Intent:
        normalized = message.lower().strip()
        if self._matches_any(normalized, self.GITHUB_PATTERNS):
            intent = Intent.GITHUB_ACTION
        elif self._matches_any(normalized, self.CODE_PATTERNS):
            intent = Intent.CODE_EXEC
        elif self._matches_any(normalized, self.DB_PATTERNS):
            intent = Intent.DB_QUERY
        elif self._matches_any(normalized, self.DOCS_PATTERNS):
            intent = Intent.DOCS_QUERY
        else:
            intent = Intent.GENERAL

        logger.info(
            "Intent: %s for message: '%s'",
            intent.value,
            message[:80],
        )
        return intent

    def _matches_any(self, text: str, patterns: list[str]) -> bool:
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

    def get_required_tools(self, intent: Intent) -> list[str]:
        tool_map = {
            Intent.DOCS_QUERY: ["rag"],
            Intent.GITHUB_ACTION: ["github"],
            Intent.CODE_EXEC: ["code_executor"],
            Intent.DB_QUERY: ["database"],
            Intent.GENERAL: [],  
        }
        return tool_map.get(intent, [])


intent_router = IntentRouter()