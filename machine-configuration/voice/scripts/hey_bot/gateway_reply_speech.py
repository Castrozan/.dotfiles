from __future__ import annotations

from dataclasses import dataclass

from assistant_gateway import GatewayReply, GatewayReplyKind

UNREACHABLE_GATEWAY_SPEECH = "Sorry, I could not reach the gateway."
UNPARSABLE_REPLY_SPEECH = "Sorry, I could not process that."


@dataclass(frozen=True)
class FailureSpeech:
    unreachable: str
    unparsable: str


def spoken_reply(reply: GatewayReply, failure_speech: FailureSpeech) -> str:
    if reply.kind is GatewayReplyKind.CONTENT:
        return reply.content
    if reply.kind is GatewayReplyKind.UNREACHABLE:
        return failure_speech.unreachable
    return failure_speech.unparsable
