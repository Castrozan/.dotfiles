import asyncio
import fcntl
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class VoiceIdentity:
    name: str
    client: Any
    token_file: str
    preferred_agent: str | None = None
    error: str | None = None
    lease: object = None


def identity_specifications(specifications, host, listener_user_id, guild_id):
    if not 1 <= len(specifications) <= 8:
        raise ValueError("voice_identity_count_out_of_bounds")
    names = set()
    token_files = set()
    selected = []
    for specification in specifications:
        if specification["ownerHost"] != host:
            continue
        if (
            int(specification["listenerUserId"]) != listener_user_id
            or int(specification["guildId"]) != guild_id
        ):
            continue
        if specification["name"] in names or specification["tokenFile"] in token_files:
            continue
        names.add(specification["name"])
        token_files.add(specification["tokenFile"])
        selected.append(specification)
    return selected


def channel_refusal(channel, member):
    permissions = channel.permissions_for(member)
    if not all((permissions.view_channel, permissions.connect, permissions.speak)):
        return "missing_voice_permissions"
    if getattr(channel, "type", None) is not None and str(channel.type) != "voice":
        return "unsupported_voice_channel"
    if member.voice and (member.voice.mute or member.voice.deaf):
        return "bot_server_muted_or_deafened"
    if channel.user_limit and len(channel.voice_states) >= channel.user_limit:
        return "voice_channel_full"
    return None


class VoiceIdentityPool:
    def __init__(self, identities, lease_directory):
        self.identities = sorted(identities, key=lambda identity: identity.name)
        self._lease_directory = Path(lease_directory)

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
        if identity.error or not identity.client.is_ready():
            return None, identity.error or "identity_not_ready"
        guild = identity.client.get_guild(guild_id)
        if guild is None or guild.me is None:
            return None, "bot_not_in_allowed_guild"
        if guild.me.voice and guild.me.voice.channel is not None:
            return (
                None,
                "owned_call"
                if identity.lease is not None
                else "bot_voice_connection_in_use",
            )
        for channel in guild.voice_channels:
            if listener_user_id in channel.voice_states:
                return channel, channel_refusal(channel, guild.me)
        return None, "listener_not_in_allowed_voice_channel"

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
                "ready": identity.client.is_ready() and identity.error is None,
                "error": identity.error,
                "owned": identity.lease is not None,
                "unavailable_reason": self.eligibility(
                    identity, listener_user_id, guild_id
                )[1],
            }
            for identity in self.identities
        ]
