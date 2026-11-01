import queue
import re
import sys
import threading
from collections import OrderedDict
from collections.abc import Callable


EPISODE_STREAM_TARGET = re.compile(
    r"(?P<episode_prefix>.*/stream/series/tt\d+(?::|%3A)\d+(?::|%3A))"
    r"(?P<episode>\d+)\.json",
    re.IGNORECASE,
)
MAXIMUM_QUEUED_TARGETS = 2
MAXIMUM_TRACKED_TARGETS = 256
FOREGROUND_WAIT_SECONDS = 45


def next_episode_target(request_target: str) -> str | None:
    stream_target = EPISODE_STREAM_TARGET.fullmatch(request_target)
    if stream_target is None:
        return None
    next_episode = int(stream_target["episode"]) + 1
    return f"{stream_target['episode_prefix']}{next_episode}.json"


class NextEpisodePrewarmer:
    def __init__(self, warm: Callable[[str], object]):
        self._warm = warm
        self._queued_targets = queue.Queue(MAXIMUM_QUEUED_TARGETS)
        self._completions: OrderedDict[str, threading.Event] = OrderedDict()
        self._lock = threading.Lock()

    def start(self) -> None:
        threading.Thread(target=self._warm_queued_targets, daemon=True).start()

    def schedule_after(self, request_target: str) -> None:
        target = next_episode_target(request_target)
        if target is None:
            return
        with self._lock:
            if target in self._completions:
                return
            completion = threading.Event()
            try:
                self._queued_targets.put_nowait((target, completion))
            except queue.Full:
                return
            self._completions[target] = completion
            while len(self._completions) > MAXIMUM_TRACKED_TARGETS:
                self._completions.popitem(last=False)

    def wait_for_warming(self, request_target: str) -> None:
        with self._lock:
            completion = self._completions.get(request_target)
        if completion is not None:
            completion.wait(FOREGROUND_WAIT_SECONDS)

    def _warm_queued_targets(self) -> None:
        while True:
            target, completion = self._queued_targets.get()
            try:
                self._warm(target)
            except Exception as error:
                print(f"episode prewarm failed: {error}", file=sys.stderr, flush=True)
            finally:
                completion.set()
