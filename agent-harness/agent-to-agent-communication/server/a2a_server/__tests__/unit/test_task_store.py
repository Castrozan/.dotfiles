import pytest

from a2a_server import task_store as task_store_module
from a2a_server.task_store import TaskStore


class FakeClock:
    def __init__(self):
        self.now_epoch_seconds = 1_000.0

    def time(self):
        return self.now_epoch_seconds


@pytest.fixture
def clock(monkeypatch):
    fake_clock = FakeClock()
    monkeypatch.setattr(task_store_module, "time", fake_clock)
    return fake_clock


class TestTaskStore:
    def test_create_task_returns_task_in_submitted_state_with_unique_id(self):
        store = TaskStore()
        task_one = store.create_task("hello")
        task_two = store.create_task("world")
        assert task_one.state == "submitted"
        assert task_two.state == "submitted"
        assert task_one.id != task_two.id
        assert task_one.input_text == "hello"
        assert task_two.input_text == "world"

    def test_transition_task_state_updates_state_and_activity_timestamp(self, clock):
        store = TaskStore()
        task = store.create_task("input")
        original_activity_timestamp = task.last_activity_at_epoch_seconds
        clock.now_epoch_seconds += 0.01
        updated_task = store.transition_task_state(task.id, "working")
        assert updated_task.state == "working"
        assert updated_task.last_activity_at_epoch_seconds > original_activity_timestamp

    def test_append_task_output_concatenates_chunks(self):
        store = TaskStore()
        task = store.create_task("input")
        store.append_task_output(task.id, "chunk-one ")
        store.append_task_output(task.id, "chunk-two")
        refreshed = store.get_task(task.id)
        assert refreshed.output_text == "chunk-one chunk-two"

    def test_mark_task_failed_with_error_message_sets_state_and_message(self):
        store = TaskStore()
        task = store.create_task("input")
        store.mark_task_failed_with_error_message(task.id, "boom")
        refreshed = store.get_task(task.id)
        assert refreshed.state == "failed"
        assert refreshed.error_message == "boom"

    def test_terminal_state_detection_recognizes_completed_canceled_failed(self):
        store = TaskStore()
        completed_task = store.create_task("input")
        canceled_task = store.create_task("input")
        failed_task = store.create_task("input")
        working_task = store.create_task("input")
        store.transition_task_state(completed_task.id, "completed")
        store.transition_task_state(canceled_task.id, "canceled")
        store.transition_task_state(failed_task.id, "failed")
        store.transition_task_state(working_task.id, "working")
        assert store.is_task_in_terminal_state(completed_task.id)
        assert store.is_task_in_terminal_state(canceled_task.id)
        assert store.is_task_in_terminal_state(failed_task.id)
        assert not store.is_task_in_terminal_state(working_task.id)

    def test_heartbeat_age_seconds_grows_over_time(self, clock):
        store = TaskStore()
        task = store.create_task("input")
        clock.now_epoch_seconds += 0.5
        assert task.heartbeat_age_seconds() >= 0.5

    def test_to_json_serializable_dict_contains_expected_keys(self):
        store = TaskStore()
        task = store.create_task("input")
        payload = task.to_json_serializable_dict()
        for expected_key in (
            "id",
            "state",
            "input",
            "output",
            "createdAt",
            "updatedAt",
            "heartbeatAgeSeconds",
            "errorMessage",
        ):
            assert expected_key in payload
