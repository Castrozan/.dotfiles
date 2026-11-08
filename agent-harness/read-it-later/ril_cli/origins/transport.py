from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Callable

ORIGIN_TEXT_CHARACTER_LIMIT = 8000
COMMAND_TIMEOUT_SECONDS = 90
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0 Safari/537.36"
)
CURL_TRAILER_FORMAT = "\n%{url_effective}\n%{content_type}"


class OriginUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchedPage:
    body: str
    effective_url: str
    content_type: str


def run_command(arguments: list[str]) -> str:
    try:
        completed = subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise OriginUnavailable(f"{arguments[0]} failed: {error}") from error
    return completed.stdout


def curl_arguments(url: str) -> list[str]:
    return [
        "curl",
        "-sSL",
        "--compressed",
        "--max-time",
        "45",
        "-A",
        BROWSER_USER_AGENT,
        "-w",
        CURL_TRAILER_FORMAT,
        url,
    ]


def fetch_page(
    url: str, command_runner: Callable[[list[str]], str] = run_command
) -> FetchedPage:
    body, effective_url, content_type = command_runner(curl_arguments(url)).rsplit(
        "\n", 2
    )
    return FetchedPage(body, effective_url.strip(), content_type.strip().lower())


def fetch_json(
    url: str, command_runner: Callable[[list[str]], str] = run_command
) -> dict:
    page = fetch_page(url, command_runner)
    try:
        return json.loads(page.body)
    except json.JSONDecodeError as error:
        raise OriginUnavailable(f"{url} answered with non-JSON content") from error


@dataclass(frozen=True)
class OriginTransport:
    command_runner: Callable[[list[str]], str] = run_command

    def page(self, url: str) -> FetchedPage:
        return fetch_page(url, self.command_runner)

    def json(self, url: str) -> dict:
        return fetch_json(url, self.command_runner)

    def run(self, arguments: list[str]) -> str:
        return self.command_runner(arguments)


def bounded_text(text: str) -> str:
    return text.strip()[:ORIGIN_TEXT_CHARACTER_LIMIT]
