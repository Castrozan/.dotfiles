import asyncio
import json
from unittest.mock import Mock

import pytest

from provider_fixtures import load_control_server, make_clip_call
from voice_provider.listener_audio_tap import SILENCE_FRAME, ListenerAudioTap
from voice_provider.capture_broadcast import CaptureBroadcast

CLIP = bytes(range(200)) * 4


def run(coroutine):
    return asyncio.run(coroutine)


async def eventually(condition):
    for _attempt in range(200):
        if condition():
            return
        await asyncio.sleep(0.005)
    raise AssertionError("condition never became true")


def test_play_then_hush_stops_the_playback_at_once(tmp_path):
    async def scenario():
        _module, call, playback, connection = make_clip_call(tmp_path)
        await call.join()
        playing = asyncio.create_task(call.play_clip(CLIP, 24000))
        await asyncio.wait_for(playback.started.wait(), 1)
        assert not playing.done()
        assert call.hush() == {"outcome": "hushed"}
        assert await asyncio.wait_for(playing, 1) == {"outcome": "interrupted"}
        assert playback.played == [(24000, CLIP)]
        connection.stop.assert_called()
        await call.leave()

    run(scenario())


def test_a_finished_clip_reports_finished(tmp_path):
    async def scenario():
        _module, call, playback, _connection = make_clip_call(tmp_path)
        await call.join()
        playing = asyncio.create_task(call.play_clip(CLIP, 16000))
        await asyncio.wait_for(playback.started.wait(), 1)
        playback.finish()
        assert await asyncio.wait_for(playing, 1) == {"outcome": "finished"}
        await call.leave()

    run(scenario())


def test_hush_also_cancels_a_clip_still_waiting_for_the_speaker(tmp_path):
    async def scenario():
        _module, call, playback, _connection = make_clip_call(tmp_path)
        await call.join()
        first = asyncio.create_task(call.play_clip(CLIP, 24000))
        await asyncio.wait_for(playback.started.wait(), 1)
        second = asyncio.create_task(call.play_clip(CLIP, 24000))
        await asyncio.sleep(0.01)
        call.hush()
        assert await asyncio.wait_for(first, 1) == {"outcome": "interrupted"}
        assert await asyncio.wait_for(second, 1) == {"outcome": "interrupted"}
        assert len(playback.played) == 1
        await call.leave()

    run(scenario())


def test_a_clip_after_a_hush_plays_normally(tmp_path):
    async def scenario():
        _module, call, playback, _connection = make_clip_call(tmp_path)
        await call.join()
        call.hush()
        playing = asyncio.create_task(call.play_clip(CLIP, 24000))
        await asyncio.wait_for(playback.started.wait(), 1)
        assert not playing.done()
        call.hush()
        await asyncio.wait_for(playing, 1)
        await call.leave()

    run(scenario())


def test_play_outside_a_call_fails_with_a_clear_error(tmp_path):
    async def scenario():
        module, call, playback, _connection = make_clip_call(tmp_path)
        with pytest.raises(module.VoiceCallError, match="not_in_voice_channel"):
            await call.play_clip(CLIP, 24000)
        assert playback.played == []

    run(scenario())


def header_line(**fields):
    return json.dumps({"command": "play", **fields}).encode() + b"\n"


async def exchange(control, request_bytes):
    server = await asyncio.start_server(control.serve_connection, "127.0.0.1", 0)
    reader, writer = await asyncio.open_connection(*server.sockets[0].getsockname())
    writer.write(request_bytes)
    await writer.drain()
    try:
        return await asyncio.wait_for(reader.readline(), 2)
    finally:
        writer.close()
        server.close()
        await control.close()
        await server.wait_closed()


def test_the_socket_refuses_play_outside_a_call_with_a_json_error(tmp_path):
    async def scenario():
        module, call, _playback, _connection = make_clip_call(tmp_path)
        control = load_control_server(module).ControlServer(call, Mock())
        reply = await exchange(
            control, header_line(sample_rate=24000, byte_count=len(CLIP)) + CLIP
        )
        assert json.loads(reply) == {"error": "not_in_voice_channel"}

    run(scenario())


def test_the_socket_plays_the_uploaded_bytes_and_answers_when_hushed(tmp_path):
    async def scenario():
        module, call, playback, _connection = make_clip_call(tmp_path)
        control = load_control_server(module).ControlServer(call, Mock())
        await call.join()
        server = await asyncio.start_server(control.serve_connection, "127.0.0.1", 0)
        address = server.sockets[0].getsockname()
        reader, writer = await asyncio.open_connection(*address)
        writer.write(header_line(sample_rate=24000, byte_count=len(CLIP)) + CLIP)
        await writer.drain()
        await asyncio.wait_for(playback.started.wait(), 1)
        hush_reader, hush_writer = await asyncio.open_connection(*address)
        hush_writer.write(b'{"command":"hush"}\n')
        await hush_writer.drain()
        assert json.loads(await asyncio.wait_for(hush_reader.readline(), 1)) == {
            "outcome": "hushed"
        }
        assert json.loads(await asyncio.wait_for(reader.readline(), 1)) == {
            "outcome": "interrupted"
        }
        assert playback.played == [(24000, CLIP)]
        for stream in (writer, hush_writer):
            stream.close()
        server.close()
        await control.close()
        await call.leave()

    run(scenario())


@pytest.mark.parametrize(
    "fields",
    [
        {"sample_rate": 0, "byte_count": 4},
        {"sample_rate": 24000, "byte_count": 0},
        {"sample_rate": 24000, "byte_count": 3},
        {"sample_rate": 24000, "byte_count": 10**12},
        {"sample_rate": True, "byte_count": 4},
        {"sample_rate": 10**7, "byte_count": 4},
        {"sample_rate": "24000", "byte_count": 4},
        {"byte_count": 4},
    ],
)
def test_a_malformed_play_header_is_refused_before_any_audio_is_read(tmp_path, fields):
    async def scenario():
        module, call, playback, _connection = make_clip_call(tmp_path)
        control = load_control_server(module).ControlServer(call, Mock())
        await call.join()
        reply = await exchange(control, header_line(**fields) + b"1234")
        assert json.loads(reply) == {"error": "invalid_request"}
        assert playback.played == []
        await call.leave()

    run(scenario())


def test_the_socket_streams_capture_silence_when_not_in_a_call(tmp_path):
    async def scenario():
        module, call, _playback, _connection = make_clip_call(tmp_path)
        broadcast = CaptureBroadcast(ListenerAudioTap())
        control = load_control_server(module).ControlServer(call, broadcast)
        server = await asyncio.start_server(control.serve_connection, "127.0.0.1", 0)
        reader, writer = await asyncio.open_connection(*server.sockets[0].getsockname())
        writer.write(b'{"command":"capture"}\n')
        await writer.drain()
        frames = [await asyncio.wait_for(reader.readexactly(640), 1) for _ in range(3)]
        assert frames == [SILENCE_FRAME] * 3
        writer.close()
        await eventually(lambda: not broadcast._subscribers)
        server.close()
        await control.close()

    run(scenario())
