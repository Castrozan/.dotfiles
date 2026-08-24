from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto

GATEWAY_TIMEOUT_SECONDS = 120
COMPLETIONS_PATH = "/v1/chat/completions"
AGENT_HEADER_NAME = "x-clawdbot-agent-id"


class GatewayReplyKind(Enum):
    CONTENT = auto()
    UNREACHABLE = auto()
    UNPARSABLE = auto()


@dataclass(frozen=True)
class GatewayReply:
    kind: GatewayReplyKind
    content: str = ""
    raw_response: str = ""


@dataclass(frozen=True)
class GatewaySettings:
    url: str
    token: str
    agent_id: str
    model: str


def parse_gateway_response(raw_response: str) -> GatewayReply:
    if not raw_response.strip():
        return GatewayReply(GatewayReplyKind.UNREACHABLE, raw_response=raw_response)
    try:
        content = json.loads(raw_response)["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        content = ""
    if not content:
        return GatewayReply(GatewayReplyKind.UNPARSABLE, raw_response=raw_response)
    return GatewayReply(GatewayReplyKind.CONTENT, content=content)


class AssistantGateway:
    def __init__(
        self,
        settings: GatewaySettings,
        open_request: Callable[..., object] = urllib.request.urlopen,
    ):
        self._settings = settings
        self._open_request = open_request

    def ask(self, message_content: str) -> GatewayReply:
        try:
            with self._open_request(
                self._build_request(message_content),
                timeout=GATEWAY_TIMEOUT_SECONDS,
            ) as response:
                raw_response = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as failure:
            return parse_gateway_response(
                failure.read().decode("utf-8", errors="replace")
            )
        except OSError:
            return GatewayReply(GatewayReplyKind.UNREACHABLE)
        return parse_gateway_response(raw_response)

    def _build_request(self, message_content: str) -> urllib.request.Request:
        payload = {
            "model": self._settings.model,
            "user": f"voice-{self._settings.agent_id}",
            "messages": [{"role": "user", "content": message_content}],
        }
        return urllib.request.Request(
            f"{self._settings.url}{COMPLETIONS_PATH}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._settings.token}",
                AGENT_HEADER_NAME: self._settings.agent_id,
            },
            method="POST",
        )
