import threading
import time
from typing import Callable

from .backends.base import AgentBackend, BackendObservation
from .task_store import Task, TaskStore

BACKGROUND_OBSERVATION_INTERVAL_SECONDS = 1.0
WORKING_TASK_IDLE_TIMEOUT_SECONDS_FOR_AUTO_COMPLETE = 30.0
TARGET_DEAD_GRACE_PERIOD_SECONDS_BEFORE_SERVER_SHUTDOWN = 15.0


class ActiveTaskCoordinator:
    def __init__(
        self,
        task_store: TaskStore,
        agent_backend: AgentBackend,
        auto_complete_idle_timeout_seconds: float = WORKING_TASK_IDLE_TIMEOUT_SECONDS_FOR_AUTO_COMPLETE,
        target_dead_grace_period_seconds: float = TARGET_DEAD_GRACE_PERIOD_SECONDS_BEFORE_SERVER_SHUTDOWN,
        on_target_died_callback: Callable[[], None] | None = None,
    ) -> None:
        self._task_store = task_store
        self._agent_backend = agent_backend
        self._auto_complete_idle_timeout_seconds = auto_complete_idle_timeout_seconds
        self._target_dead_grace_period_seconds = target_dead_grace_period_seconds
        self._on_target_died_callback = on_target_died_callback
        self._active_task_id: str | None = None
        self._target_first_observed_dead_at_epoch_seconds: float | None = None
        self._on_target_died_callback_already_fired = False
        self._lock = threading.Lock()
        self._observer_should_stop = threading.Event()
        self._observer_thread: threading.Thread | None = None

    def start_background_observation(self) -> None:
        self._observer_thread = threading.Thread(
            target=self._continuously_observe_backend_and_update_active_task,
            daemon=True,
        )
        self._observer_thread.start()

    def stop_background_observation(self) -> None:
        self._observer_should_stop.set()
        if self._observer_thread is not None:
            self._observer_thread.join(timeout=2)

    def submit_new_task_if_idle(self, input_text: str) -> tuple[Task, bool]:
        with self._lock:
            if (
                self._active_task_id is not None
                and not self._task_store.is_task_in_terminal_state(self._active_task_id)
            ):
                existing_task = self._task_store.get_task(self._active_task_id)
                return existing_task, False
            new_task = self._task_store.create_task(input_text)
            self._active_task_id = new_task.id
            self._task_store.transition_task_state(new_task.id, "working")
        self._agent_backend.send_input_text(input_text)
        return new_task, True

    def cancel_active_task_if_matches(self, task_id: str) -> Task | None:
        with self._lock:
            if self._active_task_id != task_id:
                return self._task_store.get_task(task_id)
            if self._task_store.is_task_in_terminal_state(task_id):
                return self._task_store.get_task(task_id)
        self._agent_backend.cancel_gracefully()
        return self._task_store.transition_task_state(task_id, "canceled")

    def _continuously_observe_backend_and_update_active_task(self) -> None:
        while not self._observer_should_stop.is_set():
            time.sleep(BACKGROUND_OBSERVATION_INTERVAL_SECONDS)
            self._observe_once_and_apply_to_active_task()

    def _observe_once_and_apply_to_active_task(self) -> None:
        observation = self._agent_backend.observe()
        self._apply_observation_to_active_task_if_any(observation)
        self._fire_shutdown_callback_when_target_has_been_dead_long_enough(observation)

    def _apply_observation_to_active_task_if_any(
        self, observation: BackendObservation
    ) -> None:
        with self._lock:
            active_task_id = self._active_task_id
        if active_task_id is None:
            return
        if self._task_store.is_task_in_terminal_state(active_task_id):
            return
        if observation.raw_output_since_last_call:
            self._task_store.append_task_output(
                active_task_id, observation.raw_output_since_last_call
            )
        if not observation.is_alive:
            terminal_state_for_dead_backend = (
                self._classify_terminal_state_for_dead_backend(observation)
            )
            if terminal_state_for_dead_backend == "failed":
                self._task_store.mark_task_failed_with_error_message(
                    active_task_id,
                    f"backend exited with code {observation.exit_code}",
                )
            else:
                self._task_store.transition_task_state(active_task_id, "completed")
            return
        idle_for_seconds = time.time() - observation.last_activity_at_epoch_seconds
        if idle_for_seconds >= self._auto_complete_idle_timeout_seconds:
            self._task_store.transition_task_state(active_task_id, "completed")

    @staticmethod
    def _classify_terminal_state_for_dead_backend(
        observation: BackendObservation,
    ) -> str:
        if observation.exit_code is None or observation.exit_code == 0:
            return "completed"
        return "failed"

    def _fire_shutdown_callback_when_target_has_been_dead_long_enough(
        self, observation: BackendObservation
    ) -> None:
        if observation.is_alive:
            self._target_first_observed_dead_at_epoch_seconds = None
            return
        if (
            self._on_target_died_callback is None
            or self._on_target_died_callback_already_fired
        ):
            return
        if self._target_first_observed_dead_at_epoch_seconds is None:
            self._target_first_observed_dead_at_epoch_seconds = time.time()
            return
        elapsed_since_dead_seconds = (
            time.time() - self._target_first_observed_dead_at_epoch_seconds
        )
        if elapsed_since_dead_seconds < self._target_dead_grace_period_seconds:
            return
        self._on_target_died_callback_already_fired = True
        self._on_target_died_callback()
