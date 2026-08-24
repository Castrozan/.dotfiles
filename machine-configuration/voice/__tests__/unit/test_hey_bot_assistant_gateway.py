import io
import json
import urllib.error

from hey_bot.assistant_gateway import AssistantGateway, GatewayReplyKind, GatewaySettings

SETTINGS = GatewaySettings(
    url="http://gateway.invalid",
    token="gateway-token",
    agent_id="main",
    model="test-model",
)


class FakeResponse:
    def __init__(self, body):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *_exception_details):
        return False

    def read(self):
        return self._body


def gateway_answering(body):
    sent_requests = []

    def open_request(request, timeout):
        sent_requests.append((request, timeout))
        return FakeResponse(body)

    return AssistantGateway(SETTINGS, open_request=open_request), sent_requests


def gateway_failing_with(failure):
    def open_request(_request, timeout):
        raise failure

    return AssistantGateway(SETTINGS, open_request=open_request)


def test_the_request_carries_the_model_the_voice_user_and_the_agent_headers():
    gateway, sent_requests = gateway_answering(b"{}")

    gateway.ask("the prompt")

    request, timeout = sent_requests[0]
    assert json.loads(request.data) == {
        "model": "test-model",
        "user": "voice-main",
        "messages": [{"role": "user", "content": "the prompt"}],
    }
    assert request.full_url == "http://gateway.invalid/v1/chat/completions"
    assert request.get_header("Authorization") == "Bearer gateway-token"
    assert request.get_header("X-clawdbot-agent-id") == "main"
    assert timeout == 120


def test_a_completion_body_becomes_content():
    gateway, _requests = gateway_answering(
        json.dumps(
            {"choices": [{"message": {"content": "The weather is fine."}}]}
        ).encode("utf-8")
    )

    reply = gateway.ask("the prompt")

    assert reply.kind is GatewayReplyKind.CONTENT
    assert reply.content == "The weather is fine."


def test_an_empty_body_reads_as_an_unreachable_gateway():
    gateway, _requests = gateway_answering(b"")

    assert gateway.ask("the prompt").kind is GatewayReplyKind.UNREACHABLE


def test_a_body_without_a_completion_reads_as_unparsable():
    gateway, _requests = gateway_answering(b'{"error":"upstream exploded"}')

    reply = gateway.ask("the prompt")

    assert reply.kind is GatewayReplyKind.UNPARSABLE
    assert reply.raw_response == '{"error":"upstream exploded"}'


def test_a_refused_connection_reads_as_an_unreachable_gateway():
    gateway = gateway_failing_with(urllib.error.URLError("connection refused"))

    assert gateway.ask("the prompt").kind is GatewayReplyKind.UNREACHABLE


def test_an_error_status_keeps_its_body_for_the_unparsable_report():
    gateway = gateway_failing_with(
        urllib.error.HTTPError(
            "http://gateway.invalid/v1/chat/completions",
            500,
            "Server Error",
            {},
            io.BytesIO(b'{"error":"upstream exploded"}'),
        )
    )

    reply = gateway.ask("the prompt")

    assert reply.kind is GatewayReplyKind.UNPARSABLE
    assert reply.raw_response == '{"error":"upstream exploded"}'
