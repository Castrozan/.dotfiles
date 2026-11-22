import asyncio
import logging
from pathlib import Path

PRESENCE_POLL_SECONDS = 0.1
PRESENCE_SETTLE_SECONDS = 3

logger = logging.getLogger(__name__)


def gateway_session_id(client):
    return getattr(getattr(client, "ws", None), "session_id", None)


def self_voice_state(client, guild_id):
    guild = client.get_guild(guild_id)
    if guild is None or guild.me is None:
        return None
    voice = guild.me.voice
    if voice is None or voice.channel is None:
        return None
    return voice


class VoiceSessionRecord:
    def __init__(self, directory):
        self._directory = Path(directory)

    def _path(self, bot_user_id):
        return self._directory / f"{bot_user_id}.voice-session"

    def remember(self, bot_user_id, session_id):
        if session_id is None:
            return
        self._directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._path(bot_user_id).write_text(session_id)

    def recalled(self, bot_user_id):
        try:
            return self._path(bot_user_id).read_text()
        except FileNotFoundError:
            return None

    def forget(self, bot_user_id):
        self._path(bot_user_id).unlink(missing_ok=True)


def bridge_owns_voice_state(identity, voice, record):
    if voice.session_id is None:
        return False
    return voice.session_id in {
        gateway_session_id(identity.client),
        record.recalled(identity.client.user.id),
    }


async def settle(condition, seconds=PRESENCE_SETTLE_SECONDS):
    loop = asyncio.get_running_loop()
    deadline = loop.time() + seconds
    while not condition():
        if loop.time() >= deadline:
            return False
        await asyncio.sleep(PRESENCE_POLL_SECONDS)
    return True


async def claim_voice_state(client, voice):
    session_id = gateway_session_id(client)
    if voice.session_id == session_id:
        return
    guild = voice.channel.guild
    await guild.change_voice_state(channel=voice.channel)
    await settle(
        lambda: (
            getattr(self_voice_state(client, guild.id), "session_id", session_id)
            == session_id
        )
    )


async def send_voice_state_release(client, voice):
    await claim_voice_state(client, voice)
    await voice.channel.guild.change_voice_state(channel=None)


async def release_stale_voice_state(identity, guild_id, record):
    client = identity.client
    voice = self_voice_state(client, guild_id)
    if voice is None:
        record.forget(client.user.id)
        return True
    if not bridge_owns_voice_state(identity, voice, record):
        return False
    try:
        await send_voice_state_release(client, voice)
    except Exception as error:
        logger.warning(
            "voice identity %s could not send its leave: %s",
            identity.name,
            type(error).__name__,
        )
        return False
    return await confirm_voice_state_release(identity, guild_id, record)


async def confirm_voice_state_release(identity, guild_id, record):
    client = identity.client
    if not await settle(lambda: self_voice_state(client, guild_id) is None):
        logger.warning("voice identity %s is still in a voice channel", identity.name)
        return False
    record.forget(client.user.id)
    return True
