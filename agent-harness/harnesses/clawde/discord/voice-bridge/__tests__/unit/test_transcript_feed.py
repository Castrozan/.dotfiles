import asyncio

from voice_bridge.transcript_feed import RETAINED_LINE_COUNT, TranscriptFeed


def run(coroutine):
    return asyncio.run(coroutine)


def test_a_subscriber_receives_lines_published_after_it_joined():
    async def scenario():
        feed = TranscriptFeed()
        feed.publish(text="before")
        subscriber = feed.subscribe(feed.last_sequence)
        feed.publish(text="after")
        return subscriber.get_nowait(), subscriber.empty()

    line, drained = run(scenario())

    assert line == {"sequence": 2, "text": "after"}
    assert drained


def test_a_returning_subscriber_replays_what_it_missed():
    async def scenario():
        feed = TranscriptFeed()
        for text in ("first", "second", "third"):
            feed.publish(text=text)
        subscriber = feed.subscribe(1)
        return [subscriber.get_nowait()["text"] for _ in range(2)]

    assert run(scenario()) == ["second", "third"]


def test_retention_stays_bounded():
    async def scenario():
        feed = TranscriptFeed()
        for number in range(RETAINED_LINE_COUNT + 10):
            feed.publish(text=str(number))
        return feed.subscribe(0).qsize()

    assert run(scenario()) == RETAINED_LINE_COUNT


def test_an_unsubscribed_queue_receives_nothing():
    async def scenario():
        feed = TranscriptFeed()
        subscriber = feed.subscribe(0)
        feed.unsubscribe(subscriber)
        feed.publish(text="ignored")
        return subscriber.empty()

    assert run(scenario())


def test_shutdown_closes_an_idle_transcript_follower():
    import importlib.util
    import sys
    from pathlib import Path
    from unittest.mock import Mock, patch

    source = (
        Path(__file__).resolve().parents[2] / "scripts/voice_bridge/control_server.py"
    )
    specification = importlib.util.spec_from_file_location(
        "control_server_under_test", source
    )
    module = importlib.util.module_from_spec(specification)
    with patch.dict(
        sys.modules, {"voice_bridge.voice_call": Mock(VoiceCallError=RuntimeError)}
    ):
        specification.loader.exec_module(module)

    async def scenario():
        feed = TranscriptFeed()
        control = module.ControlServer(Mock(), feed)
        server = await asyncio.start_server(control.serve_connection, "127.0.0.1", 0)
        reader, writer = await asyncio.open_connection(*server.sockets[0].getsockname())
        writer.write(b'{"command":"follow"}\n')
        await writer.drain()
        for _attempt in range(20):
            if feed._subscribers:
                break
            await asyncio.sleep(0.001)
        assert feed._subscribers
        server.close()
        try:
            await asyncio.wait_for(control.close(), timeout=0.1)
            await asyncio.wait_for(server.wait_closed(), timeout=0.1)
            assert await asyncio.wait_for(reader.read(), timeout=0.1) == b""
            assert not feed._subscribers
        finally:
            writer.close()
            await writer.wait_closed()

    run(scenario())
