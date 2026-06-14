import http.server
import threading

from .active_task_coordinator import ActiveTaskCoordinator
from .agent_card import AgentCard
from .backends.base import AgentBackend
from .http_handler import build_http_request_handler_class
from .request_router import A2ARequestRouter
from .task_store import TaskStore


def run_a2a_server_blocking(
    host: str,
    port: int,
    agent_card: AgentCard,
    agent_backend: AgentBackend,
) -> None:
    task_store = TaskStore()
    http_server_holder: dict[str, http.server.ThreadingHTTPServer] = {}

    def shutdown_http_server_in_background_thread() -> None:
        server_to_shut_down = http_server_holder.get("server")
        if server_to_shut_down is None:
            return
        threading.Thread(target=server_to_shut_down.shutdown, daemon=True).start()

    active_task_coordinator = ActiveTaskCoordinator(
        task_store,
        agent_backend,
        on_target_died_callback=shutdown_http_server_in_background_thread,
    )
    router = A2ARequestRouter(agent_card, task_store, active_task_coordinator)
    request_handler_class = build_http_request_handler_class(router)
    http_server = http.server.ThreadingHTTPServer((host, port), request_handler_class)
    http_server_holder["server"] = http_server
    agent_backend.start()
    active_task_coordinator.start_background_observation()
    try:
        http_server.serve_forever()
    finally:
        active_task_coordinator.stop_background_observation()
        agent_backend.stop()
