import asyncio
import functools
import json
import logging
import os
import signal
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import discord

from voice_bridge.control_server import ControlServer
from voice_bridge.speech_synthesis import SpeechSelection
from voice_bridge.speech_transcription import transcribe_discord_audio
from voice_bridge.transcript_feed import TranscriptFeed
from voice_bridge.voice_call import VoiceCall
from voice_identity import VoiceIdentity, VoiceIdentityPool, identity_specifications


@dataclass(frozen=True)
class CallAudioServices:
    ffmpeg: str
    synthesizer: SpeechSelection
    transcribe_audio: Callable[[bytes], str]


def discord_client():
    intents = discord.Intents.none()
    intents.guilds = True
    intents.voice_states = True
    return discord.Client(intents=intents)


async def run_bridge():
    environment = os.environ
    feed = TranscriptFeed()
    ffmpeg = environment["VOICE_BRIDGE_FFMPEG"]
    control_socket = Path(environment["VOICE_BRIDGE_CONTROL_SOCKET"])
    listener_user_id = int(environment["VOICE_BRIDGE_LISTENER_USER_ID"])
    specifications = identity_specifications(
        json.loads(Path(environment["VOICE_BRIDGE_IDENTITIES"]).read_text()),
        environment["VOICE_BRIDGE_HOST"],
        listener_user_id,
        int(environment["VOICE_BRIDGE_ANSWERED_GUILD_ID"]),
    )
    identities = VoiceIdentityPool(
        [
            VoiceIdentity(
                specification["name"],
                discord_client(),
                specification["tokenFile"],
                specification.get("preferredAgent"),
            )
            for specification in specifications
        ],
        control_socket.parent.parent / "discord-voice-identities",
    )
    call = VoiceCall(
        identities,
        listener_user_id,
        int(environment["VOICE_BRIDGE_ANSWERED_GUILD_ID"]),
        CallAudioServices(
            ffmpeg,
            SpeechSelection(
                json.loads(
                    Path(environment["VOICE_BRIDGE_CHARACTER_CATALOG"]).read_text()
                ),
                environment["VOICE_BRIDGE_CLOUD_VOICE"],
            ),
            functools.partial(transcribe_discord_audio, ffmpeg),
        ),
        feed,
    )

    control = ControlServer(call, feed)
    server = await asyncio.start_unix_server(
        control.serve_connection, path=control_socket
    )
    control_socket.chmod(0o600)

    claimed_bot_ids = set()

    async def run_identity(identity):
        client = identity.client

        @client.event
        async def on_ready():
            await call.follow_listener()

        @client.event
        async def on_voice_state_update(member, before, after):
            if member.id == listener_user_id and before.channel != after.channel:
                await call.follow_listener()
            if member.id == client.user.id and before.channel != after.channel:
                call.observe_bot_movement(identity)

        try:
            async with asyncio.timeout(30):
                await client.login(Path(identity.token_file).read_text().strip())
            if client.user.id in claimed_bot_ids:
                identity.error = "duplicate_bot_identity"
                return
            claimed_bot_ids.add(client.user.id)
            await client.connect()
        except Exception as error:
            identity.error = f"identity_unavailable_{type(error).__name__}"
            logging.warning(
                "Discord identity %s unavailable: %s",
                identity.name,
                type(error).__name__,
            )
        finally:
            await client.close()

    stop_requested = asyncio.Event()
    loop = asyncio.get_running_loop()
    for stop_signal in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(stop_signal, stop_requested.set)
    client_tasks = [
        asyncio.create_task(run_identity(identity))
        for identity in identities.identities
    ]
    try:
        await stop_requested.wait()
    finally:
        server.close()
        await control.close()
        await server.wait_closed()
        await call.leave()
        await identities.close(client_tasks)


def main():
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("discord.voice_state").setLevel(logging.INFO)
    discord.opus.load_opus(os.environ["VOICE_BRIDGE_OPUS_LIBRARY"])
    asyncio.run(run_bridge())


if __name__ == "__main__":
    main()
