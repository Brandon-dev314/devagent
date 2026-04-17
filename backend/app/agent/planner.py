import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("devagent.planner")


class StepType(str, Enum):
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    ANSWER = "answer"


class ActionType(str, Enum):
    SEARCH_DOCS = "search_docs"
    CREATE_ISSUE = "create_issue"
    SEARCH_ISSUES = "search_issues"
    EXEC_CODE = "exec_code"
    QUERY_DB = "query_db"
    NONE = "none"  


@dataclass
class PlanStep:
    step_type: StepType
    content: str
    action_type: ActionType = ActionType.NONE
    action_input: dict = field(default_factory=dict)
    result: str = ""


@dataclass
class ExecutionPlan:
    steps: list[PlanStep] = field(default_factory=list)
    max_steps: int = 5  
    current_step: int = 0

    def add_step(self, step: PlanStep) -> None:
        if len(self.steps) >= self.max_steps:
            logger.warning(
                "Plan reached max steps (%d). Forcing answer.",
                self.max_steps,
            )
            return
        self.steps.append(step)

    @property
    def is_complete(self) -> bool:
        return any(s.step_type == StepType.ANSWER for s in self.steps)

    @property
    def last_step(self) -> PlanStep | None:
        return self.steps[-1] if self.steps else None


REACT_SYSTEM_PROMPT = """You are DevAgent, an AI-powered developer support agent.

You help developers by:
1. Answering questions using technical documentation (RAG)
2. Creating GitHub issues when requested
3. Running code snippets in sandboxed environments
4. Querying databases for information

You have access to these tools:
- search_docs(query): Search technical documentation for relevant information
- create_issue(title, body): Create a GitHub issue
- search_issues(query): Search existing GitHub issues
- exec_code(code, language): Execute code in a sandboxed environment
- query_db(sql): Run a read-only SQL query

When answering questions:
- Always cite your sources when using information from documentation
- Be concise but thorough
- Include code examples when relevant
- If you don't know something, say so honestly

When using tools:
- Think step by step about what information you need
- Use the minimum number of tool calls necessary
- Explain what you're doing and why

Always respond in the same language the user writes in."""


class Planner:

    def create_plan(self, message: str, intent: str, tools: list[str]) -> ExecutionPlan:
        plan = ExecutionPlan()

        if intent == "docs_query":
            plan = self._plan_docs_query(message)
        elif intent == "github_action":
            plan = self._plan_github_action(message)
        elif intent == "code_exec":
            plan = self._plan_code_exec(message)
        elif intent == "db_query":
            plan = self._plan_db_query(message)
        else:
            plan = self._plan_general(message)

        logger.info(
            "📋 Plan created: %d steps for intent '%s'",
            len(plan.steps),
            intent,
        )
        return plan

    def _plan_docs_query(self, message: str) -> ExecutionPlan:
        plan = ExecutionPlan()

        plan.add_step(PlanStep(
            step_type=StepType.THOUGHT,
            content=f"The user is asking about documentation. I need to search for relevant information about: {message[:200]}",
        ))

        plan.add_step(PlanStep(
            step_type=StepType.ACTION,
            content="Searching documentation...",
            action_type=ActionType.SEARCH_DOCS,
            action_input={"query": message},
        ))

        plan.add_step(PlanStep(
            step_type=StepType.ANSWER,
            content="Generate response using retrieved documentation context.",
        ))

        return plan

    def _plan_github_action(self, message: str) -> ExecutionPlan:
        plan = ExecutionPlan()

        plan.add_step(PlanStep(
            step_type=StepType.THOUGHT,
            content=f"The user wants to perform a GitHub action. Analyzing request: {message[:200]}",
        ))
        lower_msg = message.lower()
        if any(word in lower_msg for word in ["create", "open", "make", "file", "submit"]):
            plan.add_step(PlanStep(
                step_type=StepType.ACTION,
                content="Creating GitHub issue...",
                action_type=ActionType.CREATE_ISSUE,
                action_input={"message": message},
            ))
        else:
            plan.add_step(PlanStep(
                step_type=StepType.ACTION,
                content="Searching GitHub issues...",
                action_type=ActionType.SEARCH_ISSUES,
                action_input={"query": message},
            ))

        plan.add_step(PlanStep(
            step_type=StepType.ANSWER,
            content="Report the result of the GitHub action.",
        ))

        return plan

    def _plan_code_exec(self, message: str) -> ExecutionPlan:
        plan = ExecutionPlan()

        plan.add_step(PlanStep(
            step_type=StepType.THOUGHT,
            content="The user wants to execute code. I need to extract the code and run it safely.",
        ))

        plan.add_step(PlanStep(
            step_type=StepType.ACTION,
            content="Executing code in sandbox...",
            action_type=ActionType.EXEC_CODE,
            action_input={"message": message},
        ))

        plan.add_step(PlanStep(
            step_type=StepType.ANSWER,
            content="Show the code execution results.",
        ))

        return plan

    def _plan_db_query(self, message: str) -> ExecutionPlan:
        plan = ExecutionPlan()

        plan.add_step(PlanStep(
            step_type=StepType.THOUGHT,
            content="The user wants to query the database. I need to generate and run a safe SQL query.",
        ))

        plan.add_step(PlanStep(
            step_type=StepType.ACTION,
            content="Running database query...",
            action_type=ActionType.QUERY_DB,
            action_input={"message": message},
        ))

        plan.add_step(PlanStep(
            step_type=StepType.ANSWER,
            content="Present the query results.",
        ))

        return plan

    def _plan_general(self, message: str) -> ExecutionPlan:
        plan = ExecutionPlan()

        plan.add_step(PlanStep(
            step_type=StepType.ANSWER,
            content="Respond directly to the user's general message.",
        ))

        return plan

planner = Planner()