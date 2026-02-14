import asyncio
import pytest

from voice_pipeline.adapters.unix_control import (
    UnixSocketControlServer,
    UnixSocketControlClient,
)


class TestUnixSocketControl:
    @pytest.mark.asyncio
    async def test_server_start_stop(self, tmp_path):
        socket_path = str(tmp_path / "test.sock")
        server = UnixSocketControlServer(socket_path=socket_path)
        await server.start()
        assert (tmp_path / "test.sock").exists()
        await server.stop()
        assert not (tmp_path / "test.sock").exists()

    @pytest.mark.asyncio
    async def test_client_server_toggle(self, tmp_path):
        socket_path = str(tmp_path / "test.sock")
        server = UnixSocketControlServer(socket_path=socket_path)
        await server.start()

        async def consume_commands():
            async for cmd in server.commands():
                assert cmd.action == "toggle"
                break

        consumer = asyncio.create_task(consume_commands())

        client = UnixSocketControlClient(socket_path=socket_path)
        result = await client.send_command("toggle")
        assert result["status"] == "ok"
        assert result["action"] == "toggle"

        await asyncio.wait_for(consumer, timeout=2.0)
        await server.stop()

    @pytest.mark.asyncio
    async def test_client_server_agent_switch(self, tmp_path):
        socket_path = str(tmp_path / "test.sock")
        server = UnixSocketControlServer(socket_path=socket_path)
        await server.start()

        async def consume_commands():
            async for cmd in server.commands():
                assert cmd.action == "agent"
                assert cmd.payload == {"name": "robson"}
                break

        consumer = asyncio.create_task(consume_commands())

        client = UnixSocketControlClient(socket_path=socket_path)
        result = await client.send_command("agent", {"name": "robson"})
        assert result["status"] == "ok"

        await asyncio.wait_for(consumer, timeout=2.0)
        await server.stop()

    @pytest.mark.asyncio
    async def test_client_connection_refused(self):
        client = UnixSocketControlClient(socket_path="/tmp/nonexistent.sock")
        with pytest.raises((ConnectionRefusedError, FileNotFoundError)):
            await client.send_command("status")
