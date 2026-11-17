import json
from unittest.mock import Mock

import mac_seat_client
import pytest
from hypothesis import given
from hypothesis import strategies as st
from websockets.sync import client


class Connection:
    def __init__(self):
        self.sent = []
        self.closed = False

    def send(self, message):
        self.sent.append(message)

    def close(self):
        self.closed = True


def stream_over(connection, rate=24000):
    opened = Mock(return_value=connection)
    return mac_seat_client.SeatStream(rate, opened), opened


@given(st.lists(st.binary(min_size=1), min_size=1, max_size=10))
def test_every_chunk_travels_in_order_over_one_connection(chunks):
    connection = Connection()
    stream, opened = stream_over(connection)
    for chunk in chunks:
        stream.send(chunk)
    assert connection.sent == chunks
    opened.assert_called_once_with(24000)


def test_nothing_connects_until_the_first_chunk_is_sent():
    stream, opened = stream_over(Connection())
    assert not opened.called
    stream.close()


def test_opening_ahead_of_the_first_chunk_connects_once():
    stream, opened = stream_over(Connection())
    stream.open()
    stream.send(b"\x01\x02")
    opened.assert_called_once_with(24000)


def test_clearing_hushes_the_seat(monkeypatch):
    hush = Mock()
    monkeypatch.setattr(mac_seat_client, "hush", hush)
    stream, opened = stream_over(Connection())
    stream.clear()
    hush.assert_called_once_with()
    assert not opened.called


def test_closing_ends_the_connection_that_was_opened():
    connection = Connection()
    stream, _ = stream_over(connection)
    stream.send(b"\x01\x02")
    stream.close()
    assert connection.closed


def test_opening_waits_for_the_page_then_names_the_rate_before_any_audio(monkeypatch):
    connection = Connection()
    connect = Mock(return_value=connection)
    waits = []
    monkeypatch.setattr(client, "connect", connect)
    monkeypatch.setattr(
        mac_seat_client.local_seat,
        "wait_until",
        lambda *arguments: waits.append(arguments),
    )
    assert mac_seat_client.open_stream_connection(24000) is connection
    assert waits == [
        (
            mac_seat_client.attached,
            mac_seat_client.STREAM_ATTACH_WAIT_SECONDS,
            mac_seat_client.NO_PAGE_MESSAGE,
        )
    ]
    assert connect.call_args.args == ("ws://127.0.0.1:8772/stream",)
    assert connect.call_args.kwargs["origin"] == mac_seat_client.ORIGIN
    assert [json.loads(message) for message in connection.sent] == [
        {"sampleRate": 24000}
    ]


def test_a_page_that_never_attaches_ends_the_stream_with_the_reason(monkeypatch):
    monkeypatch.setattr(mac_seat_client, "STREAM_ATTACH_WAIT_SECONDS", -1)
    monkeypatch.setattr(mac_seat_client, "attached", lambda: False)
    monkeypatch.setattr(client, "connect", Mock())
    with pytest.raises(TimeoutError, match="did not attach"):
        mac_seat_client.open_stream_connection(24000)
