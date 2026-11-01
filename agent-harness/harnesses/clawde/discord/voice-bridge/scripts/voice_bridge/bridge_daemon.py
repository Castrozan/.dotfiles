import asyncio
import functools
import logging
import os
import signal
from pathlib import Path

import discord

from voice_bridge.control_server import ControlServer
from voice_bridge.speech_synthesis import SpeechSynthesizer
from voice_bridge.speech_transcription import transcribe_discord_audio
from voice_bridge.transcript_feed import TranscriptFeed
from voice_bridge.voice_call import VoiceCall, VoiceCallError


def discord_client():
    intents = discord.Intents.none()
    intents.guilds = True
    intents.voice_states = True
    return discord.Client(intents=intents)


async def run_bridge():
    environment = os.environ
    client = discord_client()
    feed = TranscriptFeed()
    ffmpeg = environment["VOICE_BRIDGE_FFMPEG"]
    control_socket = Path(environment["VOICE_BRIDGE_CONTROL_SOCKET"])
    call = VoiceCall(
        client,
        int(environment["VOICE_BRIDGE_LISTENER_USER_ID"]),
        ffmpeg,
        SpeechSynthesizer(
            environment["VOICE_BRIDGE_MEDIA_SPEECH"],
            environment["VOICE_BRIDGE_CLOUD_VOICE"],
            control_socket.parent,
        ),
        functools.partial(transcribe_discord_audio, ffmpeg),
        feed,
    )

    @client.event
    async def on_ready():
        try:
            await call.join()
        except VoiceCallError as error:
            logging.info("not rejoining: %s", error)

    control = ControlServer(call, feed)

    async def serve_when_ready(reader, writer):
        await client.wait_until_ready()
        await control.serve_connection(reader, writer)

    await client.login(Path(environment["VOICE_BRIDGE_TOKEN_FILE"]).read_text().strip())
    server = await asyncio.start_unix_server(serve_when_ready, path=control_socket)
    stop_requested = asyncio.Event()
    loop = asyncio.get_running_loop()
    for stop_signal in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(stop_signal, stop_requested.set)
    client_task = asyncio.create_task(client.connect())
    stop_task = asyncio.create_task(stop_requested.wait())
    finished, _pending = await asyncio.wait(
        {client_task, stop_task}, return_when=asyncio.FIRST_COMPLETED
    )
    server.close()
    await call.leave()
    await client.close()
    if client_task in finished:
        client_task.result()


def main():
    logging.basicConfig(level=logging.WARNING)
    discord.opus.load_opus(os.environ["VOICE_BRIDGE_OPUS_LIBRARY"])
    asyncio.run(run_bridge())


if __name__ == "__main__":
    main()
