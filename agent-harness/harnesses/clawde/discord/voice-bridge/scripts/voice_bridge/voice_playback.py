import asyncio

import discord

PLAYBACK_LEAD_SILENCE_MILLISECONDS = 200


async def play_audio_file(voice_client, audio_path, ffmpeg):
    playback_finished = asyncio.Event()
    loop = asyncio.get_running_loop()
    voice_client.play(
        discord.FFmpegPCMAudio(
            audio_path,
            executable=ffmpeg,
            options=f"-af adelay={PLAYBACK_LEAD_SILENCE_MILLISECONDS}:all=1",
        ),
        after=lambda _error: loop.call_soon_threadsafe(playback_finished.set),
    )
    await playback_finished.wait()
