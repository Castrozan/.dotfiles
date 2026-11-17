import asyncio
import logging
from pathlib import Path


class IdentityConnection:
    def __init__(
        self, identity, call, listener_user_id, claimed_bot_ids, silver_channel
    ):
        self.identity = identity
        self.call = call
        self.listener_user_id = listener_user_id
        self.claimed_bot_ids = claimed_bot_ids
        self.silver_channel = silver_channel

    async def on_ready(self):
        await self.call.follow_listener()

    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return
        if member.id == self.listener_user_id:
            await self.call.follow_listener()
            await self.silver_channel.listener_moved_to(after.channel)
        if member.id == self.identity.client.user.id:
            self.call.observe_bot_movement(self.identity)

    async def login(self):
        client = self.identity.client
        async with asyncio.timeout(30):
            await client.login(Path(self.identity.token_file).read_text().strip())
        if client.user.id in self.claimed_bot_ids:
            self.identity.error = "duplicate_bot_identity"
            return False
        self.claimed_bot_ids.add(client.user.id)
        return True

    async def run(self):
        client = self.identity.client
        client.event(self.on_ready)
        client.event(self.on_voice_state_update)
        try:
            if not await self.login():
                return
            await client.connect()
        except Exception as error:
            self.identity.error = f"identity_unavailable_{type(error).__name__}"
            logging.warning(
                "Discord identity %s unavailable: %s",
                self.identity.name,
                type(error).__name__,
            )
        finally:
            await client.close()
