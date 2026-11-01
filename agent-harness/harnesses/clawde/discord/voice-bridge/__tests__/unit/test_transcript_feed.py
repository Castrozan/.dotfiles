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
