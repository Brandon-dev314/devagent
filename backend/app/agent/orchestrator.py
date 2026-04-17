import logging
from openai import AsyncOpenAI
from app.config import settings
from app.models.schemas import ChatRequest, ChatResponse, SearchResult
from app.agent.memory import ConversationMemory, memory_store
from app.agent.router import intent_router, Intent
from app.agent.planner import planner, StepType, ActionType, REACT_SYSTEM_PROMPT
from app.rag.embeddings import embedding_service
from app.rag.retrieval import retrieval_service
from app.tools import get_tool

logger = logging.getLogger("devagent.orchestrator")


class AgentOrchestrator:

    def __init__(self):
        if settings.openai_api_key:
            self.llm_client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            self.llm_client = None
            logger.warning("OpenAI API key not set. LLM responses will fail.")

    async def handle_message(self, request: ChatRequest) -> ChatResponse:
        memory = memory_store.get_or_create(
            conversation_id=request.conversation_id,
            system_prompt=REACT_SYSTEM_PROMPT,
        )

        memory.add_user_message(request.message)

        intent = intent_router.classify(request.message)
        tools_needed = intent_router.get_required_tools(intent)

        plan = planner.create_plan(
            message=request.message,
            intent=intent.value,
            tools=tools_needed,
        )

        sources: list[SearchResult] = []
        tools_used: list[str] = []
        context_text = ""

        for step in plan.steps:
            if step.step_type == StepType.THOUGHT:
                logger.info("Thought: %s", step.content[:200])

            elif step.step_type == StepType.ACTION:
                logger.info(
                    "Action: %s (%s)",
                    step.action_type.value,
                    step.content,
                )

                if step.action_type == ActionType.SEARCH_DOCS:
                    search_results = await self._search_docs(
                        step.action_input.get("query", request.message)
                    )
                    sources.extend(search_results)
                    tools_used.append("rag_search")

                    if search_results:
                        context_text = self._build_context(search_results)
                        memory.inject_context(context_text)

                    step.result = f"Found {len(search_results)} relevant documents."

                elif step.action_type == ActionType.CREATE_ISSUE:
                    tool = get_tool("create_issue")
                    if tool:
                        result = await tool.execute(
                            repo=step.action_input.get("repo", ""),
                            title=step.action_input.get("title", ""),
                            body=step.action_input.get("body", ""),
                        )
                        step.result = result.output if result.success else result.error
                        tools_used.append("github_create_issue")
                    else:
                        step.result = "GitHub tool not available."

                elif step.action_type == ActionType.EXEC_CODE:
                    tool = get_tool("exec_code")
                    if tool:
                        result = await tool.execute(
                            code=step.action_input.get("code", ""),
                            language=step.action_input.get("language", "python"),
                        )
                        step.result = result.output if result.success else result.error
                        tools_used.append("code_executor")
                    else:
                        step.result = "Code executor not available."

                elif step.action_type == ActionType.QUERY_DB:
                    tool = get_tool("query_db")
                    if tool:
                        result = await tool.execute(
                            sql=step.action_input.get("sql", ""),
                        )
                        step.result = result.output if result.success else result.error
                        tools_used.append("database")
                    else:
                        step.result = "Database tool not available."

                logger.info("Observation: %s", step.result[:200])

            elif step.step_type == StepType.ANSWER:
                pass

        response_text = await self._generate_response(memory)

        memory.add_assistant_message(response_text)

        return ChatResponse(
            message=response_text,
            conversation_id=memory.conversation_id,
            sources=sources,
            tools_used=tools_used,
        )

    async def _search_docs(self, query: str) -> list[SearchResult]:
        try:
            query_embedding = await embedding_service.aembed_query(query)
            results = await retrieval_service.search(
                query_embedding=query_embedding,
                top_k=settings.top_k,
                score_threshold=0.5,
            )
            return results
        except Exception as e:
            logger.error("❌ RAG search failed: %s", e)
            return []

    def _build_context(self, results: list[SearchResult]) -> str:
        context_parts = []
        for result in results:
            source = result.chunk.metadata.source
            score = result.score
            text = result.chunk.text

            context_parts.append(
                f"--- Source: {source} (relevance: {score:.2f}) ---\n{text}"
            )

        return "\n\n".join(context_parts)

    async def _generate_response(self, memory: ConversationMemory) -> str:
        if not self.llm_client:
            return (
                "I'm unable to generate a response because the OpenAI API key "
                "is not configured. Please set OPENAI_API_KEY in your .env file."
            )

        try:
            messages = memory.get_messages_for_llm()

            response = await self.llm_client.chat.completions.create(
                model=settings.llm_model,
                messages=messages, # type: ignore
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )

            content = response.choices[0].message.content or ""
            logger.info(
                "LLM response generated (%d tokens)",
                response.usage.completion_tokens if response.usage else 0,
            )
            return content

        except Exception as e:
            logger.error("LLM generation failed: %s", e, exc_info=True)
            return f"I encountered an error generating a response: {str(e)}"

orchestrator = AgentOrchestrator()