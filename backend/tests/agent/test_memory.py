from app.agent.memory import ConversationMemory, MemoryStore

class TestConversationMemory:
    def test_new_conversation_has_id(self):
        memory = ConversationMemory()
        assert memory.conversation_id
        assert len(memory.conversation_id) > 0

    def test_custom_conversation_id(self):
        memory = ConversationMemory(conversation_id="test-123")
        assert memory.conversation_id == "test-123"

    def test_new_conversation_is_empty(self):
        memory = ConversationMemory()
        assert memory.is_empty
        assert memory.message_count == 0

    def test_add_user_message(self):
        memory = ConversationMemory()
        msg = memory.add_user_message("Hello!")

        assert memory.message_count == 1
        assert not memory.is_empty
        assert msg.role == "user"
        assert msg.content == "Hello!"

    def test_add_assistant_message(self):
        memory = ConversationMemory()
        memory.add_user_message("Hi")
        msg = memory.add_assistant_message("Hello! How can I help?")

        assert memory.message_count == 2
        assert msg.role == "assistant"

    def test_messages_for_llm_includes_system_prompt(self):
        memory = ConversationMemory(system_prompt="You are a helpful agent.")
        memory.add_user_message("Hello")

        messages = memory.get_messages_for_llm()

        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful agent."
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    def test_messages_for_llm_without_system_prompt(self):
        memory = ConversationMemory(system_prompt="")
        memory.add_user_message("Hello")

        messages = memory.get_messages_for_llm()
        assert messages[0]["role"] == "user"

    def test_sliding_window_truncates(self):
        memory = ConversationMemory(
            system_prompt="System",
            window_size=3,
        )
        for i in range(10):
            memory.add_user_message(f"User message {i}")
            memory.add_assistant_message(f"Assistant response {i}")

        messages = memory.get_messages_for_llm()
        assert len(messages) == 7
        assert messages[0]["role"] == "system"
        assert "7" in messages[1]["content"]

    def test_full_history_preserved(self):
        memory = ConversationMemory(window_size=2)

        for i in range(10):
            memory.add_user_message(f"Message {i}")
        assert memory.message_count == 10

    def test_inject_context(self):
        memory = ConversationMemory()
        memory.add_user_message("How do I use FastAPI?")
        memory.inject_context("FastAPI is a modern web framework...")

        messages = memory.get_messages_for_llm()
        system_messages = [m for m in messages if m["role"] == "system"]
        assert any("FastAPI" in m["content"] for m in system_messages)

    def test_clear_resets_history(self):
        memory = ConversationMemory()
        memory.add_user_message("Hello")
        memory.add_assistant_message("Hi!")

        memory.clear()
        assert memory.is_empty
        assert memory.message_count == 0


class TestMemoryStore:
    def test_create_new_conversation(self):
        store = MemoryStore()
        memory = store.get_or_create(system_prompt="Test")

        assert memory.conversation_id
        assert store.active_conversations == 1

    def test_get_existing_conversation(self):
        store = MemoryStore()
        memory1 = store.get_or_create()
        conv_id = memory1.conversation_id

        memory1.add_user_message("First message")

        memory2 = store.get_or_create(conversation_id=conv_id)
        assert memory2.message_count == 1
        assert memory2 is memory1

    def test_delete_conversation(self):
        store = MemoryStore()
        memory = store.get_or_create()
        conv_id = memory.conversation_id

        assert store.delete(conv_id) is True
        assert store.active_conversations == 0

    def test_delete_nonexistent_returns_false(self):
        store = MemoryStore()
        assert store.delete("nonexistent") is False

    def test_get_nonexistent_returns_none(self):
        store = MemoryStore()
        assert store.get("nonexistent") is None

    def test_multiple_conversations(self):
        store = MemoryStore()

        memory_a = store.get_or_create()
        memory_b = store.get_or_create()

        memory_a.add_user_message("Hello from A")
        memory_b.add_user_message("Hello from B")

        assert store.active_conversations == 2
        assert memory_a.message_count == 1
        assert memory_b.message_count == 1