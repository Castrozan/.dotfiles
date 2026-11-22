import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RETRY_INITIAL_SECONDS = 1
RETRY_MAXIMUM_SECONDS = 60
RETRY_DOUBLINGS = 6


def retry_delay(consecutive_failures):
    doublings = min(consecutive_failures, RETRY_DOUBLINGS)
    return min(RETRY_MAXIMUM_SECONDS, RETRY_INITIAL_SECONDS * 2**doublings)


@dataclass(frozen=True)
class IdentityLogin:
    claimed_bot_ids: dict[int, str]
    client_factory: Callable[[], Any]
    permanent_failures: tuple[type[Exception], ...]
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep


class IdentityConnection:
    def __init__(self, identity, call, listener_user_id, silver_channel, login):
        self.identity = identity
        self.call = call
        self.listener_user_id = listener_user_id
        self.silver_channel = silver_channel
        self.identity_login = login
        self.consecutive_failures = 0

    async def on_ready(self):
        self.consecutive_failures = 0
        await self.call.release_stale_voice_state(self.identity)
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
        owner = self.identity_login.claimed_bot_ids.setdefault(
            client.user.id, self.identity.name
        )
        if owner != self.identity.name:
            self.identity.error = "duplicate_bot_identity"
            return False
        self.identity.error = None
        return True

    async def run(self):
        while not await self.attempt_connection():
            delay = retry_delay(self.consecutive_failures)
            logging.warning(
                "Discord identity %s unavailable: %s; retrying in %ss",
                self.identity.name,
                self.identity.error,
                delay,
            )
            await self.identity_login.sleep(delay)
            self.consecutive_failures += 1
            self.identity.client = self.identity_login.client_factory()

    async def attempt_connection(self):
        client = self.identity.client
        client.event(self.on_ready)
        client.event(self.on_voice_state_update)
        try:
            if await self.login():
                await client.connect()
            return True
        except self.identity_login.permanent_failures as error:
            self.identity.error = f"identity_unavailable_{type(error).__name__}"
            logging.warning(
                "Discord identity %s unavailable: %s",
                self.identity.name,
                self.identity.error,
            )
            return True
        except Exception as error:
            self.identity.error = f"identity_retrying_after_{type(error).__name__}"
            return False
        finally:
            await client.close()
