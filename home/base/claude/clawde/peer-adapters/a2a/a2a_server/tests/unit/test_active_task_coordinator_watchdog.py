import time

from a2a_server.active_task_coordinator import ActiveTaskCoordinator
from a2a_server.backends.base import AgentBackend, BackendObservation
from a2a_server.task_store import TaskStore


class ScriptedAgentBackend(AgentBackend):
    def __init__(self, observations_to_return: list[BackendObservation]) -> None:
        self._observations_to_return = observations_to_return
        self._next_index = 0
        self.input_text_invocations: list[str] = []
        self.cancel_was_called = False

    def start(self) -> None:
        return None

    def send_input_text(self, text: str) -> None:
        self.input_text_invocations.append(text)

    def observe(self) -> BackendObservation:
        if self._next_index < len(self._observations_to_return):
            observation = self._observations_to_return[self._next_index]
            self._next_index += 1
            return observation
        return self._observations_to_return[-1]

    def cancel_gracefully(self) -> None:
        self.cancel_was_called = True

    def stop(self) -> None:
        return None


def _alive_observation_with_no_new_output() -> BackendObservation:
    return BackendObservation(
        raw_output_since_last_call="",
        is_alive=True,
        last_activity_at_epoch_seconds=time.time(),
    )


def _dead_observation_with_no_new_output() -> BackendObservation:
    return BackendObservation(
        raw_output_since_last_call="",
        is_alive=False,
        last_activity_at_epoch_seconds=time.time(),
    )


class TestActiveTaskCoordinatorWatchdog:
    def test_shutdown_callback_does_not_fire_while_target_remains_alive(self):
        callback_invocations = []
        backend = ScriptedAgentBackend([_alive_observation_with_no_new_output()])
        coordinator = ActiveTaskCoordinator(
            TaskStore(),
            backend,
            target_dead_grace_period_seconds=0.0,
            on_target_died_callback=lambda: callback_invocations.append(time.time()),
        )
        coordinator._observe_once_and_apply_to_active_task()
        coordinator._observe_once_and_apply_to_active_task()
        assert callback_invocations == []

    def test_shutdown_callback_fires_after_grace_period_of_target_dead(self):
        callback_invocations = []
        backend = ScriptedAgentBackend([_dead_observation_with_no_new_output()])
        coordinator = ActiveTaskCoordinator(
            TaskStore(),
            backend,
            target_dead_grace_period_seconds=0.05,
            on_target_died_callback=lambda: callback_invocations.append(time.time()),
        )
        coordinator._observe_once_and_apply_to_active_task()
        time.sleep(0.07)
        coordinator._observe_once_and_apply_to_active_task()
        assert len(callback_invocations) == 1

    def test_shutdown_callback_fires_exactly_once_even_across_many_dead_observations(
        self,
    ):
        callback_invocations = []
        backend = ScriptedAgentBackend([_dead_observation_with_no_new_output()])
        coordinator = ActiveTaskCoordinator(
            TaskStore(),
            backend,
            target_dead_grace_period_seconds=0.0,
            on_target_died_callback=lambda: callback_invocations.append(time.time()),
        )
        coordinator._observe_once_and_apply_to_active_task()
        coordinator._observe_once_and_apply_to_active_task()
        coordinator._observe_once_and_apply_to_active_task()
        coordinator._observe_once_and_apply_to_active_task()
        assert len(callback_invocations) == 1

    def test_target_returning_to_alive_resets_dead_timer(self):
        callback_invocations = []
        scripted = [
            _dead_observation_with_no_new_output(),
            _alive_observation_with_no_new_output(),
            _dead_observation_with_no_new_output(),
        ]
        backend = ScriptedAgentBackend(scripted)
        coordinator = ActiveTaskCoordinator(
            TaskStore(),
            backend,
            target_dead_grace_period_seconds=0.1,
            on_target_died_callback=lambda: callback_invocations.append(time.time()),
        )
        coordinator._observe_once_and_apply_to_active_task()
        time.sleep(0.05)
        coordinator._observe_once_and_apply_to_active_task()
        coordinator._observe_once_and_apply_to_active_task()
        assert callback_invocations == []

    def test_shutdown_callback_is_optional(self):
        backend = ScriptedAgentBackend([_dead_observation_with_no_new_output()])
        coordinator = ActiveTaskCoordinator(
            TaskStore(),
            backend,
            target_dead_grace_period_seconds=0.0,
            on_target_died_callback=None,
        )
        coordinator._observe_once_and_apply_to_active_task()
        coordinator._observe_once_and_apply_to_active_task()
