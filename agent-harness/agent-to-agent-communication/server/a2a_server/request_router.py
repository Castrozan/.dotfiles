import json

from .active_task_coordinator import ActiveTaskCoordinator
from .agent_card import AgentCard
from .task_store import Task, TaskStore


def serialize_task_to_json_bytes(task: Task) -> bytes:
    return json.dumps(task.to_json_serializable_dict()).encode("utf-8")


class A2ARequestRouter:
    def __init__(
        self,
        agent_card: AgentCard,
        task_store: TaskStore,
        active_task_coordinator: ActiveTaskCoordinator,
    ) -> None:
        self._agent_card = agent_card
        self._task_store = task_store
        self._active_task_coordinator = active_task_coordinator

    def serve_agent_card(self) -> tuple[int, str, bytes]:
        return 200, "application/json", self._agent_card.serialize_to_json_bytes()

    def serve_health_probe(self) -> tuple[int, str, bytes]:
        return 200, "application/json", json.dumps({"status": "ok"}).encode("utf-8")

    def submit_task_from_request_body(
        self, request_body_bytes: bytes
    ) -> tuple[int, str, bytes]:
        try:
            parsed_body = json.loads(request_body_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return (
                400,
                "application/json",
                json.dumps({"error": "invalid_json"}).encode("utf-8"),
            )
        input_text = parsed_body.get("input")
        if not isinstance(input_text, str) or not input_text:
            return (
                400,
                "application/json",
                json.dumps({"error": "missing_input_field"}).encode("utf-8"),
            )
        task, was_accepted = self._active_task_coordinator.submit_new_task_if_idle(
            input_text
        )
        status_code = 201 if was_accepted else 409
        return status_code, "application/json", serialize_task_to_json_bytes(task)

    def get_task_status_by_id(self, task_id: str) -> tuple[int, str, bytes]:
        task = self._task_store.get_task(task_id)
        if task is None:
            return (
                404,
                "application/json",
                json.dumps({"error": "task_not_found"}).encode("utf-8"),
            )
        return 200, "application/json", serialize_task_to_json_bytes(task)

    def cancel_task_by_id(self, task_id: str) -> tuple[int, str, bytes]:
        task = self._active_task_coordinator.cancel_active_task_if_matches(task_id)
        if task is None:
            return (
                404,
                "application/json",
                json.dumps({"error": "task_not_found"}).encode("utf-8"),
            )
        return 200, "application/json", serialize_task_to_json_bytes(task)
