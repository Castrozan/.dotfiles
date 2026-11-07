import asyncio

import discord

PLAYBACK_LEAD_SILENCE_MILLISECONDS = 200


def streamed_pcm_input(sample_rate):
    return f"-f s16le -ar {sample_rate} -ch_layout mono"


async def play_audio_stream(voice_client, audio_stream, sample_rate, ffmpeg):
    playback_finished = asyncio.Event()
    loop = asyncio.get_running_loop()
    voice_client.play(
        discord.FFmpegPCMAudio(
            audio_stream,
            executable=ffmpeg,
            pipe=True,
            before_options=streamed_pcm_input(sample_rate),
            options=f"-af adelay={PLAYBACK_LEAD_SILENCE_MILLISECONDS}:all=1",
        ),
        after=lambda _error: loop.call_soon_threadsafe(playback_finished.set),
    )
    await playback_finished.wait()
