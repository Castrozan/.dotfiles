import asyncio
import fcntl
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from voice_permissions import (
    channel_refusal,
    guild_listener_channel,
    identity_guild,
    join_refusal,
    occupancy_refusal,
    ready_identity,
)
from voice_presence import (
    VoiceSessionRecord,
    bridge_owns_voice_state,
    release_stale_voice_state,
    self_voice_state,
)

logger = logging.getLogger(__name__)


@dataclass
class VoiceIdentity:
    name: str
    client: Any
    token_file: str
    preferred_agent: str | None = None
    error: str | None = None
    lease: object = None


class VoiceIdentityPool:
    def __init__(self, identities, lease_directory):
        self.identities = sorted(identities, key=lambda identity: identity.name)
        self._lease_directory = Path(lease_directory)
        self.voice_sessions = VoiceSessionRecord(lease_directory)

    def candidates(self, listener_user_id, guild_id, preferred=None):
        for identity in sorted(
            self.identities,
            key=lambda identity: (
                identity.name != preferred and identity.preferred_agent != preferred,
                identity.name,
            ),
        ):
            channel, refusal = self.eligibility(identity, listener_user_id, guild_id)
            if refusal is None:
                yield identity, channel

    def eligibility(self, identity, listener_user_id, guild_id):
        guild, refusal = identity_guild(identity, guild_id)
        if refusal:
            return None, refusal
        busy = occupancy_refusal(
            identity, guild.me, self.bridge_owned_voice_state(identity, guild_id)
        )
        if busy:
            return None, busy
        channel = guild_listener_channel(guild, listener_user_id)
        if channel is None:
            return None, "listener_not_in_allowed_voice_channel"
        return channel, channel_refusal(channel, guild.me)

    def bridge_owned_voice_state(self, identity, guild_id):
        voice = self_voice_state(identity.client, guild_id)
        return voice is not None and bridge_owns_voice_state(
            identity, voice, self.voice_sessions
        )

    def join_refusal(self, listener_user_id, guild_id):
        return join_refusal(self.identities, listener_user_id, guild_id)

    async def release_stale_voice_state(self, identity, guild_id):
        return await release_stale_voice_state(identity, guild_id, self.voice_sessions)

    async def connect(self, listener_user_id, guild_id, preferred):
        for identity, channel in self.candidates(listener_user_id, guild_id, preferred):
            if not self.reserve(identity):
                continue
            connection = await self._connect_candidate(
                identity, channel, listener_user_id
            )
            if connection is not None:
                return identity, connection
        return None

    def remember_voice_session(self, identity, guild_id):
        voice = self_voice_state(identity.client, guild_id)
        self.voice_sessions.remember(
            identity.client.user.id, getattr(voice, "session_id", None)
        )

    async def _connect_reserved(self, identity, channel, listener_user_id):
        await self.release_stale_voice_state(identity, channel.guild.id)
        if (
            self.eligibility(identity, listener_user_id, channel.guild.id)[1]
            is not None
        ):
            self.release(identity)
            return None
        return await channel.connect(timeout=20, reconnect=True)

    async def _connect_candidate(self, identity, channel, listener_user_id):
        try:
            return await self._connect_reserved(identity, channel, listener_user_id)
        except BaseException as error:
            self.release(identity)
            if not isinstance(error, Exception):
                raise
            logger.warning(
                "voice identity %s join failed: %s", identity.name, type(error).__name__
            )
            return None

    def reserve(self, identity):
        self._lease_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        lease = (self._lease_directory / f"{identity.client.user.id}.lock").open("a")
        try:
            fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lease.close()
            return False
        identity.lease = lease
        return True

    def release(self, identity):
        if identity.lease is not None:
            identity.lease.close()
            identity.lease = None

    async def close(self, client_tasks):
        await asyncio.gather(*(identity.client.close() for identity in self.identities))
        for task in client_tasks:
            task.cancel()
        await asyncio.gather(*client_tasks, return_exceptions=True)

    def status(self, listener_user_id, guild_id):
        return [
            {
                "name": identity.name,
                "bot_user_id": str(identity.client.user.id)
                if identity.client.user
                else None,
                "ready": ready_identity(identity),
                "error": identity.error,
                "owned": identity.lease is not None,
                "stale_voice_state": identity.lease is None
                and self.bridge_owned_voice_state(identity, guild_id),
                "unavailable_reason": self.eligibility(
                    identity, listener_user_id, guild_id
                )[1],
            }
            for identity in self.identities
        ]
