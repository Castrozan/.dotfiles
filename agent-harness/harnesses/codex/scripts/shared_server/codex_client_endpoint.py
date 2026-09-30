import asyncio
import os
from uuid import uuid4

from websockets.asyncio.server import unix_serve

from codex_client_context import ClientContext
from codex_client_transport import MAXIMUM_MESSAGE_BYTES, forward_connection
from codex_daemon import DaemonLease


class ClientEndpoint:
    def __init__(
        self, directory, environment, configuration, process_identifier, expired
    ):
        self.environment = environment
        self.configuration = configuration
        self.expired = expired
        self.process_identifier = process_identifier
        self.socket = directory / (uuid4().hex + ".sock")
        self.lease = DaemonLease(environment["CODEX_LAUNCHER_BINARY"], environment)
        self.listener = None
        self.client = None
        self.expiration = None

    def owner_is_alive(self):
        try:
            os.kill(self.process_identifier, 0)
            return True
        except ProcessLookupError:
            return False

    async def expire_when_owner_exits(self):
        if self.owner_is_alive():
            self.schedule_expiration()
        else:
            await self.expired(self)

    async def start(self):
        try:
            await asyncio.to_thread(self.lease.ensure_running)
            self.listener = await unix_serve(
                self.connect,
                str(self.socket),
                max_size=MAXIMUM_MESSAGE_BYTES,
                max_queue=4,
            )
            self.socket.chmod(0o600)
            self.schedule_expiration()
        except BaseException:
            self.lease.close()
            raise

    def schedule_expiration(self):
        self.expiration = asyncio.get_running_loop().call_later(
            30,
            lambda: asyncio.create_task(self.expire_when_owner_exits()),
        )

    async def connect(self, client):
        if self.client is not None:
            await client.close(
                code=1008, reason="This Codex client is already connected"
            )
            return
        self.expiration.cancel()
        self.client = client
        context = ClientContext(
            self.lease.directory, self.environment, self.configuration
        )
        try:
            socket = await asyncio.to_thread(self.lease.ensure_running)
            await forward_connection(
                client, socket, context, self.configuration, self.environment
            )
        except (OSError, RuntimeError):
            await client.close(code=1011, reason="Codex shared server unavailable")
        finally:
            context.close()
            self.client = None
            self.schedule_expiration()

    async def close(self):
        if self.expiration:
            self.expiration.cancel()
        if self.listener:
            self.listener.close()
            await self.listener.wait_closed()
        if self.expiration:
            self.expiration.cancel()
        self.socket.unlink(missing_ok=True)
        self.lease.close()
