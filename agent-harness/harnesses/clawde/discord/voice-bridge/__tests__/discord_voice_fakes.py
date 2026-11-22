from types import SimpleNamespace
from unittest.mock import Mock

from voice_identity import VoiceIdentity, VoiceIdentityPool
from voice_identity_fixtures import load_call_module

LISTENER_USER_ID = 42
GUILD_ID = 1
BOT_USER_ID = 100
CHANNEL_ID = 10


class FakeVoiceServer:
    def __init__(self):
        self.voice_states = {}

    def update_voice_state(self, user_id, session_id, channel):
        current = self.voice_states.get(user_id)
        if channel is not None:
            self.voice_states[user_id] = SimpleNamespace(
                session_id=session_id, channel=channel, mute=False, deaf=False
            )
            return
        if current is not None and current.session_id == session_id:
            del self.voice_states[user_id]

    def listener_joins(self, channel):
        self.update_voice_state(LISTENER_USER_ID, "listener-session", channel)

    def bot_session(self):
        voice = self.voice_states.get(BOT_USER_ID)
        return None if voice is None else voice.session_id


class FakeVoiceClient:
    def __init__(self, channel):
        self.channel = channel
        self.connected = True
        self.stop = Mock()

    def is_connected(self):
        return self.connected

    async def disconnect(self, force=False):
        self.connected = False
        try:
            await self.channel.guild.change_voice_state(channel=None)
        except ConnectionError:
            return


class FakeVoiceChannel:
    id = CHANNEL_ID
    name = "General"
    type = "voice"
    user_limit = 0

    def __init__(self, guild):
        self.guild = guild

    @property
    def voice_states(self):
        return {
            user_id: voice
            for user_id, voice in self.guild.server.voice_states.items()
            if voice.channel.id == self.id
        }

    def permissions_for(self, _member):
        return SimpleNamespace(view_channel=True, connect=True, speak=True)

    async def connect(self, timeout, reconnect):
        await self.guild.change_voice_state(channel=self)
        return FakeVoiceClient(self)


class FakeGuild:
    id = GUILD_ID
    name = "guild"

    def __init__(self, server, client):
        self.server = server
        self.client = client
        self.voice_channels = [FakeVoiceChannel(self)]

    @property
    def me(self):
        return SimpleNamespace(id=BOT_USER_ID, voice=self.cached_voice_state())

    def cached_voice_state(self):
        voice = self.server.voice_states.get(BOT_USER_ID)
        if voice is None:
            return None
        channel = next(
            channel for channel in self.voice_channels if channel.id == voice.channel.id
        )
        return SimpleNamespace(
            session_id=voice.session_id, channel=channel, mute=False, deaf=False
        )

    async def change_voice_state(self, *, channel, self_mute=False, self_deaf=False):
        self.client.sent_voice_states.append(channel)
        if not self.client.gateway_open:
            raise ConnectionResetError("Cannot write to closing transport")
        self.server.update_voice_state(BOT_USER_ID, self.client.ws.session_id, channel)


class FakeDiscordClient:
    def __init__(self, server, session_id="first-session"):
        self.user = SimpleNamespace(id=BOT_USER_ID)
        self.ws = SimpleNamespace(session_id=session_id)
        self.gateway_open = True
        self.sent_voice_states = []
        self.guild = FakeGuild(server, self)

    def is_ready(self):
        return True

    def get_guild(self, guild_id):
        return self.guild if guild_id == GUILD_ID else None

    def fresh_session(self, session_id):
        self.ws = SimpleNamespace(session_id=session_id)


def bridge_process(server, lease_directory, session_id="first-session"):
    module = load_call_module()
    module.ListenerVoiceReceiver = Mock(return_value=Mock(listener_packet_count=0))
    client = FakeDiscordClient(server, session_id)
    identity = VoiceIdentity("primary", client, "unused")
    services = SimpleNamespace(ffmpeg="ffmpeg", listener_audio=Mock())
    pool = VoiceIdentityPool([identity], lease_directory)
    call = module.VoiceCall(pool, LISTENER_USER_ID, GUILD_ID, services)
    return SimpleNamespace(module=module, client=client, identity=identity, call=call)


def server_with_listener():
    server = FakeVoiceServer()
    server.listener_joins(SimpleNamespace(id=CHANNEL_ID))
    return server
