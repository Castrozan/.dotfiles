import asyncio
import json
import logging
import os
import signal
from dataclasses import dataclass
from pathlib import Path

import discord

from voice_bridge.control_server import ControlServer
from voice_connection import IdentityConnection, IdentityLogin
from voice_identity import VoiceIdentity, VoiceIdentityPool
from voice_permissions import identity_specifications
from silver_channel import SilverChannel
from voice_provider.capture_broadcast import CaptureBroadcast
from voice_provider.clip_voice_call import ClipVoiceCall
from voice_provider.listener_audio_tap import ListenerAudioTap


@dataclass(frozen=True)
class CallAudioServices:
    ffmpeg: str
    listener_audio: ListenerAudioTap


def discord_client():
    intents = discord.Intents.none()
    intents.guilds = True
    intents.voice_states = True
    return discord.Client(intents=intents)


async def run_bridge():
    environment = os.environ
    ffmpeg = environment["VOICE_BRIDGE_FFMPEG"]
    control_socket = Path(environment["VOICE_BRIDGE_CONTROL_SOCKET"])
    listener_user_id = int(environment["VOICE_BRIDGE_LISTENER_USER_ID"])
    guild_id = int(environment["VOICE_BRIDGE_ANSWERED_GUILD_ID"])
    specifications = identity_specifications(
        json.loads(Path(environment["VOICE_BRIDGE_IDENTITIES"]).read_text()),
        environment["VOICE_BRIDGE_HOST"],
        listener_user_id,
        guild_id,
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
    silver_channel_name = environment["VOICE_BRIDGE_SILVER_CHANNEL_NAME"]
    listener_audio = ListenerAudioTap()
    call = ClipVoiceCall(
        identities,
        listener_user_id,
        guild_id,
        CallAudioServices(ffmpeg, listener_audio),
    )
    silver_channel = SilverChannel(guild_id, silver_channel_name)

    control = ControlServer(call, CaptureBroadcast(listener_audio))
    server = await asyncio.start_unix_server(
        control.serve_connection, path=control_socket
    )
    control_socket.chmod(0o600)

    login = IdentityLogin(
        {}, discord_client, (discord.LoginFailure, discord.PrivilegedIntentsRequired)
    )

    stop_requested = asyncio.Event()
    loop = asyncio.get_running_loop()
    for stop_signal in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(stop_signal, stop_requested.set)
    client_tasks = [
        asyncio.create_task(
            IdentityConnection(
                identity, call, listener_user_id, silver_channel, login
            ).run()
        )
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
    logging.getLogger("discord.gateway").setLevel(logging.INFO)
    discord.opus.load_opus(os.environ["VOICE_BRIDGE_OPUS_LIBRARY"])
    asyncio.run(run_bridge())


if __name__ == "__main__":
    main()
