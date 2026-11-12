import time

import pytest

import room_audio


class ClosedPipe:
    def write(self, chunk):
        raise BrokenPipeError(32, "Broken pipe")

    def flush(self):
        pass


class DeadPlayback:
    stdin = ClosedPipe()

    def terminate(self):
        pass


def test_a_dead_playback_stops_the_voice_loudly_instead_of_muting_it(monkeypatch):
    monkeypatch.setattr(room_audio, "playback", lambda *arguments: DeadPlayback())
    speaker = room_audio.Speaker(24000, (room_audio.LIP_SYNC_SINK,))
    speaker.play(bytes(4800))
    deadline = time.monotonic() + 2
    while speaker.failure is None and time.monotonic() < deadline:
        time.sleep(0.01)
    with pytest.raises(BrokenPipeError):
        speaker.play(bytes(4800))
