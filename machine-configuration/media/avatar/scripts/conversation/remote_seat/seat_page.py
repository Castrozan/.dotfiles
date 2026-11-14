import dataclasses
import http
import json
import sys
import urllib.parse

from websockets.datastructures import Headers
from websockets.http11 import Response

HEALTH_PATH = "/health"
FAILURE_PATH = "/failure"
LEVELS_PATH = "/levels"
HTML = "text/html; charset=utf-8"
JAVASCRIPT = "text/javascript"


@dataclasses.dataclass(frozen=True)
class PageRequest:
    connection: object
    headers: object
    path: str
    query: str


def body_response(body, content_type):
    headers = Headers(
        [
            ("Content-Type", content_type),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
            ("Connection", "close"),
        ]
    )
    return Response(http.HTTPStatus.OK, "OK", headers, body)


def refuse_unknown_path(asked):
    return asked.connection.respond(http.HTTPStatus.NOT_FOUND, "")


def seat_page_files(page_directory):
    return {
        "/": (page_directory / "index.html", HTML),
        "/seat.js": (page_directory / "seat.js", JAVASCRIPT),
        "/meeting-seat.js": (page_directory / "meeting-seat.js", JAVASCRIPT),
        "/seat-microphone.js": (page_directory / "seat-microphone.js", JAVASCRIPT),
        "/seat-audio-worklets.js": (
            page_directory / "seat-audio-worklets.js",
            JAVASCRIPT,
        ),
    }


class SeatPage:
    def __init__(
        self, page_files, seat_is_attached, levels_requested=None, host_state=dict
    ):
        self.page_files = page_files
        self.seat_is_attached = seat_is_attached
        self.levels_requested = levels_requested
        self.host_state = host_state
        self.failure = None
        self.answers = {
            HEALTH_PATH: self.report_health,
            FAILURE_PATH: self.record_failure,
            **dict.fromkeys(page_files, self.serve_file),
        }
        if levels_requested:
            self.answers[LEVELS_PATH] = self.request_levels

    def answer(self, connection, request):
        path, _, query = request.path.partition("?")
        answer = self.answers.get(path, refuse_unknown_path)
        return answer(PageRequest(connection, request.headers, path, query))

    def report_health(self, asked):
        health = {
            "attached": self.seat_is_attached(),
            "failure": self.failure,
            **self.host_state(),
        }
        return body_response(json.dumps(health).encode(), "application/json")

    def record_failure(self, asked):
        if asked.headers.get("Sec-Fetch-Site") != "same-origin":
            return asked.connection.respond(http.HTTPStatus.FORBIDDEN, "")
        self.failure = urllib.parse.unquote(asked.query)
        print(f"The seat page failed: {self.failure}", file=sys.stderr)
        return body_response(b"", "text/plain")

    def request_levels(self, asked):
        if asked.headers.get("Sec-Fetch-Site", "same-origin") != "same-origin":
            return asked.connection.respond(http.HTTPStatus.FORBIDDEN, "")
        self.levels_requested()
        return body_response(b"", "text/plain")

    def serve_file(self, asked):
        file, content_type = self.page_files[asked.path]
        return body_response(file.read_bytes(), content_type)
