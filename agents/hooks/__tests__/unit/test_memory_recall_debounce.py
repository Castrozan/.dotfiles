import time

import memory_recall


class TestShouldSkipDueToDebounce:
    def test_no_state_means_no_skip(self):
        assert not memory_recall.should_skip_due_to_debounce({}, {"api"})

    def test_stale_state_means_no_skip(self):
        state = {
            "last_fire_timestamp": time.time() - memory_recall.DEBOUNCE_SECONDS - 10,
            "last_keywords": ["api"],
        }
        assert not memory_recall.should_skip_due_to_debounce(state, {"api"})

    def test_fresh_state_with_full_overlap_skips(self):
        state = {
            "last_fire_timestamp": time.time(),
            "last_keywords": ["api", "server"],
        }
        assert memory_recall.should_skip_due_to_debounce(state, {"api", "server"})

    def test_within_hard_floor_skips_even_without_overlap(self):
        state = {
            "last_fire_timestamp": time.time(),
            "last_keywords": ["api"],
        }
        assert memory_recall.should_skip_due_to_debounce(state, {"discord"})

    def test_outside_hard_floor_with_no_overlap_does_not_skip(self):
        state = {
            "last_fire_timestamp": time.time()
            - memory_recall.DEBOUNCE_HARD_FLOOR_SECONDS
            - 1,
            "last_keywords": ["api"],
        }
        assert not memory_recall.should_skip_due_to_debounce(state, {"discord"})

    def test_within_hard_floor_skips_even_with_empty_keywords(self):
        state = {
            "last_fire_timestamp": time.time(),
            "last_keywords": ["api"],
        }
        assert memory_recall.should_skip_due_to_debounce(state, set())

    def test_outside_hard_floor_with_empty_keywords_does_not_skip(self):
        state = {
            "last_fire_timestamp": time.time()
            - memory_recall.DEBOUNCE_HARD_FLOOR_SECONDS
            - 1,
            "last_keywords": ["api"],
        }
        assert not memory_recall.should_skip_due_to_debounce(state, set())
