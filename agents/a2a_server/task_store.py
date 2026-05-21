import dataclasses
import threading
import time
import uuid
from typing import Literal

TaskState = Literal[
    "submitted", "working", "input_required", "completed", "canceled", "failed"
]

TERMINAL_TASK_STATES: frozenset[TaskState] = frozenset(
    {"completed", "canceled", "failed"}
)


@dataclasses.dataclass
class Task:
    id: str
    state: TaskState
    input_text: str
    output_text: str
    created_at_epoch_seconds: float
    updated_at_epoch_seconds: float
    last_activity_at_epoch_seconds: float
    error_message: str | None = None

    def heartbeat_age_seconds(self) -> float:
        return time.time() - self.last_activity_at_epoch_seconds

    def to_json_serializable_dict(self) -> dict:
        return {
            "id": self.id,
            "state": self.state,
            "input": self.input_text,
            "output": self.output_text,
            "createdAt": self.created_at_epoch_seconds,
            "updatedAt": self.updated_at_epoch_seconds,
            "heartbeatAgeSeconds": self.heartbeat_age_seconds(),
            "errorMessage": self.error_message,
        }


class TaskStore:
    def __init__(self) -> None:
        self._tasks_by_id: dict[str, Task] = {}
        self._lock = threading.Lock()

    def create_task(self, input_text: str) -> Task:
        with self._lock:
            now_epoch_seconds = time.time()
            task = Task(
                id=str(uuid.uuid4()),
                state="submitted",
                input_text=input_text,
                output_text="",
                created_at_epoch_seconds=now_epoch_seconds,
                updated_at_epoch_seconds=now_epoch_seconds,
                last_activity_at_epoch_seconds=now_epoch_seconds,
            )
            self._tasks_by_id[task.id] = task
            return task

    def get_task(self, task_id: str) -> Task | None:
        with self._lock:
            return self._tasks_by_id.get(task_id)

    def transition_task_state(self, task_id: str, new_state: TaskState) -> Task | None:
        with self._lock:
            task = self._tasks_by_id.get(task_id)
            if task is None:
                return None
            task.state = new_state
            task.updated_at_epoch_seconds = time.time()
            task.last_activity_at_epoch_seconds = time.time()
            return task

    def append_task_output(self, task_id: str, output_chunk: str) -> Task | None:
        with self._lock:
            task = self._tasks_by_id.get(task_id)
            if task is None:
                return None
            task.output_text += output_chunk
            task.last_activity_at_epoch_seconds = time.time()
            return task

    def mark_task_failed_with_error_message(
        self, task_id: str, error_message: str
    ) -> Task | None:
        with self._lock:
            task = self._tasks_by_id.get(task_id)
            if task is None:
                return None
            task.state = "failed"
            task.error_message = error_message
            task.updated_at_epoch_seconds = time.time()
            task.last_activity_at_epoch_seconds = time.time()
            return task

    def list_tasks(self) -> list[Task]:
        with self._lock:
            return list(self._tasks_by_id.values())

    def is_task_in_terminal_state(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks_by_id.get(task_id)
            if task is None:
                return False
            return task.state in TERMINAL_TASK_STATES
