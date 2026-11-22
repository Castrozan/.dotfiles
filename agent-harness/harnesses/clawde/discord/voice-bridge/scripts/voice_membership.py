import asyncio
import uuid
from dataclasses import dataclass
from collections.abc import Callable

from voice_permissions import guild_listener_channel


class VoiceCallError(Exception):
    pass


@dataclass(frozen=True)
class CallAudioLifecycle:
    start: Callable[[], None]
    stop: Callable[[], None]


class VoiceMembership:
    def __init__(self, identities, listener_user_id, guild_id, audio_lifecycle):
        self.identities = identities
        self.listener_user_id = listener_user_id
        self.guild_id = guild_id
        self.audio_lifecycle = audio_lifecycle
        self.identity = None
        self.voice_client = None
        self.following = False
        self.generation = uuid.uuid4().hex
        self._lock = asyncio.Lock()

    def channel(self):
        if self.voice_client is None:
            return None
        if not self.voice_client.is_connected():
            return None
        return self.voice_client.channel

    def listener_channel(self):
        if self.identity is None:
            return None
        guild = self.identity.client.get_guild(self.guild_id)
        if guild is None:
            return None
        return guild_listener_channel(guild, self.listener_user_id)

    def channel_status(self):
        channel = self.channel()
        if channel is None:
            return dict(
                joined=False,
                listener_present=False,
                channel=None,
                guild=None,
                channel_id=None,
                guild_id=None,
            )
        return dict(
            joined=True,
            listener_present=self.listener_user_id in channel.voice_states,
            channel=channel.name,
            guild=channel.guild.name,
            channel_id=str(channel.id),
            guild_id=str(channel.guild.id),
        )

    def status(self):
        return {
            **self.channel_status(),
            "generation": self.generation,
            "following": self.following,
            "bot": self.identity.name if self.identity else None,
            "identities": self.identities.status(self.listener_user_id, self.guild_id),
        }

    async def follow_listener(self):
        if not self.following:
            return
        if self.identity is None:
            await self._rejoin_if_available()
            return
        if self.listener_channel() is None:
            async with self._lock:
                await self._disconnect()
            return
        await self.join(follow=True, automatic=True)

    async def _rejoin_if_available(self):
        candidate = next(
            self.identities.candidates(self.listener_user_id, self.guild_id), None
        )
        if candidate is not None:
            await self.join(follow=True, automatic=True)

    def observe_bot_movement(self, identity):
        if identity is not self.identity:
            return
        self.generation = uuid.uuid4().hex
        if self.voice_client is not None:
            self.voice_client.stop()

    def _already_joined(self):
        channel = self.listener_channel()
        return channel is not None and self.channel() == channel

    async def join(self, preferred=None, follow=False, automatic=False):
        async with self._lock:
            if automatic and not self.following:
                return
            if self._already_joined():
                self.following = follow
                return
            await self._disconnect()
            await self._attach_call(preferred)
            self.following = follow

    async def _attach_call(self, preferred):
        selected = await self.identities.connect(
            self.listener_user_id, self.guild_id, preferred
        )
        if selected is None:
            raise VoiceCallError(
                self.identities.join_refusal(self.listener_user_id, self.guild_id)
            )
        self.identity, self.voice_client = selected
        try:
            self.identities.remember_voice_session(self.identity, self.guild_id)
            self.audio_lifecycle.start()
        except BaseException:
            await self._disconnect()
            raise

    async def leave(self):
        async with self._lock:
            self.following = False
            await self._disconnect()

    async def release_stale_voice_state(self, identity):
        async with self._lock:
            if identity is self.identity:
                return
            await self.identities.release_stale_voice_state(identity, self.guild_id)

    async def _disconnect(self):
        self.generation = uuid.uuid4().hex
        self.audio_lifecycle.stop()
        if self.voice_client is not None:
            self.voice_client.stop()
            await self.voice_client.disconnect()
            self.voice_client = None
        if self.identity is None:
            return
        try:
            await self.identities.release_stale_voice_state(
                self.identity, self.guild_id
            )
        finally:
            self.identities.release(self.identity)
            self.identity = None
