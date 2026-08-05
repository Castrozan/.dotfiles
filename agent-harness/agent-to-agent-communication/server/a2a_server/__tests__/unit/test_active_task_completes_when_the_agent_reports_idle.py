import time

from a2a_server.active_task_coordinator import ActiveTaskCoordinator
from a2a_server.backends.base import AgentBackend, BackendObservation
from a2a_server.backends.herdr_backend import agent_status_means_the_agent_is_busy
from a2a_server.task_store import TaskStore


class ReplayingAgentBackend(AgentBackend):
    def __init__(self, observations_to_replay: list[BackendObservation]) -> None:
        self._observations_to_replay = observations_to_replay
        self._next_observation_index = 0

    def start(self) -> None:
        return None

    def send_input_text(self, text: str) -> None:
        return None

    def observe(self) -> BackendObservation:
        if self._next_observation_index < len(self._observations_to_replay):
            observation = self._observations_to_replay[self._next_observation_index]
            self._next_observation_index += 1
            return observation
        return self._observations_to_replay[-1]

    def cancel_gracefully(self) -> None:
        return None

    def stop(self) -> None:
        return None


def observation_with_reported_busy_state(agent_is_busy) -> BackendObservation:
    return BackendObservation(
        raw_output_since_last_call="",
        is_alive=True,
        last_activity_at_epoch_seconds=time.time(),
        agent_is_busy=agent_is_busy,
    )


def coordinator_over(observations: list[BackendObservation]) -> ActiveTaskCoordinator:
    return ActiveTaskCoordinator(
        TaskStore(),
        ReplayingAgentBackend(observations),
        auto_complete_idle_timeout_seconds=3600.0,
    )


class TestCompletionFromTheReportedAgentStatus:
    def test_a_task_completes_as_soon_as_the_agent_goes_back_to_idle(self):
        coordinator = coordinator_over(
            [
                observation_with_reported_busy_state(True),
                observation_with_reported_busy_state(False),
            ]
        )
        task, _ = coordinator.submit_new_task_if_idle("do the thing")
        coordinator._observe_once_and_apply_to_active_task()
        coordinator._observe_once_and_apply_to_active_task()
        assert coordinator._task_store.get_task(task.id).state == "completed"

    def test_an_agent_idle_before_it_ever_worked_does_not_complete_the_task(self):
        coordinator = coordinator_over([observation_with_reported_busy_state(False)])
        task, _ = coordinator.submit_new_task_if_idle("do the thing")
        coordinator._observe_once_and_apply_to_active_task()
        coordinator._observe_once_and_apply_to_active_task()
        assert coordinator._task_store.get_task(task.id).state == "working"

    def test_a_backend_reporting_no_status_falls_back_to_the_idle_timer(self):
        coordinator = ActiveTaskCoordinator(
            TaskStore(),
            ReplayingAgentBackend([observation_with_reported_busy_state(None)]),
            auto_complete_idle_timeout_seconds=0.0,
        )
        task, _ = coordinator.submit_new_task_if_idle("do the thing")
        coordinator._observe_once_and_apply_to_active_task()
        assert coordinator._task_store.get_task(task.id).state == "completed"

    def test_a_second_task_does_not_inherit_the_first_task_busy_observation(self):
        coordinator = coordinator_over(
            [
                observation_with_reported_busy_state(True),
                observation_with_reported_busy_state(False),
                observation_with_reported_busy_state(False),
            ]
        )
        first_task, _ = coordinator.submit_new_task_if_idle("first")
        coordinator._observe_once_and_apply_to_active_task()
        coordinator._observe_once_and_apply_to_active_task()
        second_task, was_accepted = coordinator.submit_new_task_if_idle("second")
        coordinator._observe_once_and_apply_to_active_task()
        assert was_accepted
        assert first_task.id != second_task.id
        assert coordinator._task_store.get_task(second_task.id).state == "working"


class TestHerdrAgentStatusReading:
    def test_working_and_blocked_both_mean_the_turn_is_still_running(self):
        assert agent_status_means_the_agent_is_busy("working") is True
        assert agent_status_means_the_agent_is_busy("blocked") is True

    def test_idle_means_the_turn_is_over(self):
        assert agent_status_means_the_agent_is_busy("idle") is False

    def test_a_missing_status_reports_nothing_rather_than_guessing(self):
        assert agent_status_means_the_agent_is_busy(None) is None
        assert agent_status_means_the_agent_is_busy(17) is None
