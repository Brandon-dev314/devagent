import uuid
import logging
from datetime import datetime, timezone
from typing import Any
from app.models.schemas import ChatMessage

logger = logging.getLogger("devagent.memory")
DEFAULT_WINDOW_SIZE = 20


class ConversationMemory:
    def __init__(
        self,
        conversation_id: str | None = None,
        system_prompt: str = "",
        window_size: int = DEFAULT_WINDOW_SIZE,
    ):
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.system_prompt = system_prompt
        self.window_size = window_size

        self._full_history: list[ChatMessage] = []
        self.created_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)

    def add_user_message(self, content: str) -> ChatMessage:
        message = ChatMessage(role="user", content=content)
        self._full_history.append(message)
        self.last_activity = datetime.now(timezone.utc)
        logger.debug(
            "[%s] User: %s",
            self.conversation_id[:8],
            content[:100],
        )
        return message

    def add_assistant_message(self, content: str) -> ChatMessage:
        message = ChatMessage(role="assistant", content=content)
        self._full_history.append(message)
        self.last_activity = datetime.now(timezone.utc)
        return message

    def get_messages_for_llm(self) -> list[dict[str, Any]]:
        messages = []
        if self.system_prompt:
            messages.append({"role": "system","content": self.system_prompt})
        window = self._full_history[-(self.window_size * 2):]

        for msg in window:
            messages.append({"role": msg.role,"content": msg.content})

        return messages

    def inject_context(self, context: str) -> None:
        context_message = ChatMessage(
            role="system",
            content=f"Relevant documentation context:\n\n{context}",
        )
        self._full_history.append(context_message)

    @property
    def message_count(self) -> int:
        return len(self._full_history)

    @property
    def is_empty(self) -> bool:
        return len(self._full_history) == 0

    def clear(self) -> None:
        self._full_history.clear()


class MemoryStore:
    def __init__(self):
        self._conversations: dict[str, ConversationMemory] = {}

    def get_or_create(
        self,
        conversation_id: str | None = None,
        system_prompt: str = "",
    ) -> ConversationMemory:
        if conversation_id and conversation_id in self._conversations:
            return self._conversations[conversation_id]

        memory = ConversationMemory(
            conversation_id=conversation_id,
            system_prompt=system_prompt,
        )
        self._conversations[memory.conversation_id] = memory

        logger.info(
            "New conversation created: %s",
            memory.conversation_id[:8],
        )
        return memory

    def get(self, conversation_id: str) -> ConversationMemory | None:
        return self._conversations.get(conversation_id)

    def delete(self, conversation_id: str) -> bool:
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False

    @property
    def active_conversations(self) -> int:
        return len(self._conversations)


memory_store = MemoryStore()