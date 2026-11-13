import asyncio
import statistics
import subprocess

import pulse_audio
from audio_effects import CHANNELS

READ_TIMEOUT_SECONDS = 5


def sink_gain(sink):
    if sink["mute"] or not sink["volume"]:
        return 0.0
    percents = [
        float(channel["value_percent"].rstrip("%"))
        for channel in sink["volume"].values()
    ]
    return min(max(statistics.mean(percents) / 100, 0.0), 1.0)


def levels_from_sinks(sinks):
    by_name = {sink["name"]: sink for sink in sinks}
    return {
        channel: sink_gain(by_name[name])
        for channel, name in CHANNELS.items()
        if name in by_name
    }


async def current():
    try:
        sinks = await asyncio.wait_for(
            asyncio.to_thread(pulse_audio.items, "sinks"), READ_TIMEOUT_SECONDS
        )
    except (OSError, subprocess.SubprocessError, TimeoutError):
        return {}
    return levels_from_sinks(sinks)
