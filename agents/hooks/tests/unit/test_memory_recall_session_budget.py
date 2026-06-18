import memory_recall


class TestHashRecallPathSet:
    def test_hash_is_order_independent(self):
        assert memory_recall.hash_recall_path_set(
            ["/a/one.md", "/a/two.md"]
        ) == memory_recall.hash_recall_path_set(["/a/two.md", "/a/one.md"])

    def test_distinct_sets_hash_differently(self):
        assert memory_recall.hash_recall_path_set(
            ["/a/one.md"]
        ) != memory_recall.hash_recall_path_set(["/a/two.md"])


class TestHasRecallSessionBudgetBeenExhausted:
    def test_empty_state_is_not_exhausted(self):
        assert not memory_recall.has_recall_session_budget_been_exhausted({})

    def test_event_count_at_budget_is_exhausted(self):
        state = {"recall_event_count": memory_recall.SESSION_RECALL_EVENT_BUDGET}
        assert memory_recall.has_recall_session_budget_been_exhausted(state)

    def test_character_total_at_budget_is_exhausted(self):
        state = {
            "recall_character_total": memory_recall.SESSION_RECALL_CHARACTER_BUDGET
        }
        assert memory_recall.has_recall_session_budget_been_exhausted(state)

    def test_below_both_budgets_is_not_exhausted(self):
        state = {
            "recall_event_count": memory_recall.SESSION_RECALL_EVENT_BUDGET - 1,
            "recall_character_total": memory_recall.SESSION_RECALL_CHARACTER_BUDGET - 1,
        }
        assert not memory_recall.has_recall_session_budget_been_exhausted(state)


class TestWasRecallPathSetAlreadyInjected:
    def test_unseen_path_set_is_not_already_injected(self):
        assert not memory_recall.was_recall_path_set_already_injected({}, ["/a/one.md"])

    def test_recorded_path_set_is_already_injected(self):
        state = {
            "injected_recall_path_set_hashes": [
                memory_recall.hash_recall_path_set(["/a/one.md"])
            ]
        }
        assert memory_recall.was_recall_path_set_already_injected(state, ["/a/one.md"])

    def test_path_set_match_ignores_order(self):
        state = {
            "injected_recall_path_set_hashes": [
                memory_recall.hash_recall_path_set(["/a/one.md", "/a/two.md"])
            ]
        }
        assert memory_recall.was_recall_path_set_already_injected(
            state, ["/a/two.md", "/a/one.md"]
        )


class TestRecordRecallInjection:
    def test_injection_increments_counters_and_records_hash(self, tmp_path):
        state_path = tmp_path / "memory-recall-session.json"
        memory_recall.record_recall_injection(state_path, ["/a/one.md"], 42)
        state = memory_recall.load_debounce_state(state_path)
        assert state["recall_event_count"] == 1
        assert state["recall_character_total"] == 42
        assert memory_recall.was_recall_path_set_already_injected(state, ["/a/one.md"])

    def test_repeated_set_increments_count_without_duplicating_hash(self, tmp_path):
        state_path = tmp_path / "memory-recall-session.json"
        memory_recall.record_recall_injection(state_path, ["/a/one.md"], 42)
        memory_recall.record_recall_injection(state_path, ["/a/one.md"], 42)
        state = memory_recall.load_debounce_state(state_path)
        assert state["recall_event_count"] == 2
        assert state["recall_character_total"] == 84
        assert len(state["injected_recall_path_set_hashes"]) == 1

    def test_injection_preserves_existing_debounce_fields(self, tmp_path):
        state_path = tmp_path / "memory-recall-session.json"
        memory_recall.persist_debounce_state(state_path, ["api", "server"])
        memory_recall.record_recall_injection(state_path, ["/a/one.md"], 10)
        state = memory_recall.load_debounce_state(state_path)
        assert state["last_keywords"] == ["api", "server"]
        assert state["recall_event_count"] == 1


class TestPersistDebounceStatePreservesBudgetFields:
    def test_persist_after_injection_keeps_budget_and_hash_fields(self, tmp_path):
        state_path = tmp_path / "memory-recall-session.json"
        memory_recall.record_recall_injection(state_path, ["/a/one.md"], 1234)
        memory_recall.persist_debounce_state(state_path, ["fresh", "keywords"])
        state = memory_recall.load_debounce_state(state_path)
        assert state["recall_event_count"] == 1
        assert state["recall_character_total"] == 1234
        assert memory_recall.was_recall_path_set_already_injected(state, ["/a/one.md"])
        assert state["last_keywords"] == ["fresh", "keywords"]
