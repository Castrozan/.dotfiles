import http.server
import json
from typing import Callable

from .request_router import A2ARequestRouter


def route_get_request_to_router_method(
    router: A2ARequestRouter, request_path: str
) -> Callable[[], tuple[int, str, bytes]]:
    if request_path == "/.well-known/agent.json":
        return router.serve_agent_card
    if request_path == "/health":
        return router.serve_health_probe
    if request_path.startswith("/tasks/"):
        task_id = request_path[len("/tasks/") :]
        return lambda: router.get_task_status_by_id(task_id)
    return lambda: (
        404,
        "application/json",
        json.dumps({"error": "not_found"}).encode("utf-8"),
    )


def route_post_request_to_router_method(
    router: A2ARequestRouter, request_path: str, request_body_bytes: bytes
) -> Callable[[], tuple[int, str, bytes]]:
    if request_path == "/tasks/send":
        return lambda: router.submit_task_from_request_body(request_body_bytes)
    if request_path.startswith("/tasks/") and request_path.endswith("/cancel"):
        task_id = request_path[len("/tasks/") : -len("/cancel")]
        return lambda: router.cancel_task_by_id(task_id)
    return lambda: (
        404,
        "application/json",
        json.dumps({"error": "not_found"}).encode("utf-8"),
    )


def build_http_request_handler_class(
    router: A2ARequestRouter,
) -> type[http.server.BaseHTTPRequestHandler]:
    class _A2AHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            handler = route_get_request_to_router_method(router, self.path)
            self._respond_with_router_result(handler)

        def do_POST(self) -> None:
            handler = route_post_request_to_router_method(
                router, self.path, self._read_request_body_bytes()
            )
            self._respond_with_router_result(handler)

        def log_message(self, format: str, *args) -> None:
            return

        def _read_request_body_bytes(self) -> bytes:
            content_length_header = self.headers.get("Content-Length", "0")
            try:
                content_length_bytes = int(content_length_header)
            except ValueError:
                content_length_bytes = 0
            if content_length_bytes <= 0:
                return b""
            return self.rfile.read(content_length_bytes)

        def _respond_with_router_result(
            self, router_method_call: Callable[[], tuple[int, str, bytes]]
        ) -> None:
            try:
                status_code, content_type, body_bytes = router_method_call()
            except Exception as router_exception:
                error_body = json.dumps(
                    {"error": "internal_error", "detail": str(router_exception)}
                ).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(error_body)))
                self.end_headers()
                self.wfile.write(error_body)
                return
            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body_bytes)))
            self.end_headers()
            self.wfile.write(body_bytes)

    return _A2AHTTPRequestHandler
