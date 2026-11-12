import dataclasses
import http
import json
import sys
import urllib.parse

from websockets.datastructures import Headers
from websockets.http11 import Response

HEALTH_PATH = "/health"
FAILURE_PATH = "/failure"
PAGE_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/seat.js": ("seat.js", "text/javascript"),
    "/seat-audio-worklets.js": ("seat-audio-worklets.js", "text/javascript"),
}


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


class SeatPage:
    def __init__(self, page_directory, seat_is_attached):
        self.page_directory = page_directory
        self.seat_is_attached = seat_is_attached
        self.failure = None
        self.answers = {
            HEALTH_PATH: self.report_health,
            FAILURE_PATH: self.record_failure,
            **dict.fromkeys(PAGE_FILES, self.serve_file),
        }

    def answer(self, connection, request):
        path, _, query = request.path.partition("?")
        answer = self.answers.get(path, refuse_unknown_path)
        return answer(PageRequest(connection, request.headers, path, query))

    def report_health(self, asked):
        health = {"attached": self.seat_is_attached(), "failure": self.failure}
        return body_response(json.dumps(health).encode(), "application/json")

    def record_failure(self, asked):
        if asked.headers.get("Sec-Fetch-Site") != "same-origin":
            return asked.connection.respond(http.HTTPStatus.FORBIDDEN, "")
        self.failure = urllib.parse.unquote(asked.query)
        print(f"The seat page failed: {self.failure}", file=sys.stderr)
        return body_response(b"", "text/plain")

    def serve_file(self, asked):
        name, content_type = PAGE_FILES[asked.path]
        return body_response((self.page_directory / name).read_bytes(), content_type)
