import memory_recall


class TestExtractKeywordsFromText:
    def test_filters_english_stop_words(self):
        keywords = memory_recall.extract_keywords_from_text("the api is broken today")
        assert "the" not in keywords
        assert "is" not in keywords
        assert "api" in keywords
        assert "broken" in keywords

    def test_filters_portuguese_stop_words(self):
        keywords = memory_recall.extract_keywords_from_text("o servidor não funciona")
        assert "não" not in keywords
        assert "servidor" in keywords
        assert "funciona" in keywords

    def test_filters_tokens_below_min_length(self):
        keywords = memory_recall.extract_keywords_from_text("ab abc abcd")
        assert "ab" not in keywords
        assert "abc" in keywords
        assert "abcd" in keywords

    def test_dedupes_repeated_tokens(self):
        keywords = memory_recall.extract_keywords_from_text("api api server api")
        assert keywords.count("api") == 1

    def test_caps_at_max_keywords(self):
        text = " ".join(f"keyword{index}" for index in range(50))
        keywords = memory_recall.extract_keywords_from_text(text)
        assert len(keywords) <= memory_recall.MAX_KEYWORDS

    def test_lowercases_all_keywords(self):
        keywords = memory_recall.extract_keywords_from_text("APIClient ServerError")
        assert "apiclient" in keywords
        assert "servererror" in keywords

    def test_returns_empty_on_empty_text(self):
        assert memory_recall.extract_keywords_from_text("") == []

    def test_handles_punctuation(self):
        keywords = memory_recall.extract_keywords_from_text("api.client, server-error!")
        assert "api" in keywords
        assert "client" in keywords
        assert "server" in keywords
        assert "error" in keywords


class TestCollectStringsFromToolInput:
    def test_handles_plain_string(self):
        assert (
            memory_recall.collect_strings_from_tool_input("hello world")
            == "hello world"
        )

    def test_handles_dict_values(self):
        result = memory_recall.collect_strings_from_tool_input(
            {"command": "ls -la", "path": "/tmp/x"}
        )
        assert "ls -la" in result
        assert "/tmp/x" in result

    def test_handles_nested_structures(self):
        result = memory_recall.collect_strings_from_tool_input(
            {"args": ["a", "b"], "meta": {"key": "value"}}
        )
        assert "a" in result
        assert "b" in result
        assert "value" in result

    def test_handles_none_and_numbers(self):
        assert memory_recall.collect_strings_from_tool_input(None) == ""
        assert memory_recall.collect_strings_from_tool_input(42) == ""
