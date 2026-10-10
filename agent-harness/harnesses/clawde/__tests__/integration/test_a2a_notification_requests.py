import http.client
import json

import pytest
from a2a_test_client import request_json


def test_request_limit_counts_wire_bytes_and_rejects_oversized_headers_before_reading(
    owned_fleet,
):
    document = {"claimedSender": "peer", "content": "result"}
    encoded = json.dumps(document).encode()
    connection = http.client.HTTPConnection(
        owned_fleet.endpoint.removeprefix("http://"), timeout=2
    )
    try:
        connection.request(
            "POST",
            "/agents/owned-peer/messages",
            body=encoded + b" " * (8192 - len(encoded)),
        )
        response = connection.getresponse()
        assert response.status == 202
        response.read()
        connection.putrequest("POST", "/agents/owned-peer/messages")
        connection.putheader("Content-Length", "8193")
        connection.endheaders()
        response = connection.getresponse()
        assert response.status == 413
        response.read()
    finally:
        connection.close()
    assert (
        len(
            request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1][
                "messages"
            ]
        )
        == 1
    )
    assert owned_fleet.target.commands == []


@pytest.mark.parametrize(
    "body",
    [
        [],
        None,
        {},
        {"claimedSender": "peer"},
        {"claimedSender": 1, "content": "result"},
        {"claimedSender": "peer", "content": 1},
    ],
)
def test_invalid_notifications_do_not_touch_the_terminal_or_store(owned_fleet, body):
    assert (
        request_json(owned_fleet, "POST", "/agents/owned-peer/messages", body)[0] == 400
    )
    assert (
        request_json(owned_fleet, "GET", "/agents/owned-peer/messages")[1]["messages"]
        == []
    )
    assert owned_fleet.target.commands == []
