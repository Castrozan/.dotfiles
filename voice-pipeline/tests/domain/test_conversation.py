from voice_pipeline.domain.conversation import ConversationHistory


class TestConversationHistory:
    def test_add_user_message(self):
        conv = ConversationHistory()
        conv.add_user_message("hello")
        assert len(conv.messages) == 1
        assert conv.messages[0].role == "user"
        assert conv.messages[0].content == "hello"

    def test_add_assistant_message(self):
        conv = ConversationHistory()
        conv.add_assistant_message("hi there")
        assert len(conv.messages) == 1
        assert conv.messages[0].role == "assistant"

    def test_multi_turn(self):
        conv = ConversationHistory()
        conv.add_user_message("hello")
        conv.add_assistant_message("hi")
        conv.add_user_message("how are you")
        assert len(conv.messages) == 3

    def test_trim_at_max_turns(self):
        conv = ConversationHistory(max_turns=2)
        for i in range(5):
            conv.add_user_message(f"user {i}")
            conv.add_assistant_message(f"assistant {i}")
        assert len(conv.messages) == 4
        assert conv.messages[0].content == "user 3"

    def test_truncate_last_assistant_message(self):
        conv = ConversationHistory()
        conv.add_user_message("tell me a story")
        conv.add_assistant_message("Once upon a time in a land far far away there lived a dragon")
        conv.truncate_last_assistant_message("Once upon a time")
        assert conv.messages[-1].content == "Once upon a time [interrupted]"

    def test_truncate_empty_spoken_removes_message(self):
        conv = ConversationHistory()
        conv.add_user_message("tell me a story")
        conv.add_assistant_message("Once upon a time")
        conv.truncate_last_assistant_message("")
        assert len(conv.messages) == 1

    def test_clear(self):
        conv = ConversationHistory()
        conv.add_user_message("hello")
        conv.add_assistant_message("hi")
        conv.clear()
        assert len(conv.messages) == 0

    def test_to_api_messages_with_system(self):
        conv = ConversationHistory()
        conv.add_user_message("hello")
        result = conv.to_api_messages(system_prefix="Be concise")
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"

    def test_to_api_messages_without_system(self):
        conv = ConversationHistory()
        conv.add_user_message("hello")
        result = conv.to_api_messages()
        assert len(result) == 1
        assert result[0]["role"] == "user"
