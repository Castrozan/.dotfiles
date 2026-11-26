import asyncio
import json
from unittest.mock import AsyncMock, Mock

import approve
from app_server import CodexConfigurationClient, CodexStdioConnection
from launch_arguments import HookDiscoveryRequest
import pytest


def test_client_ignores_notifications_and_correlates_responses():
    process = Mock()
    process.stdin.drain = AsyncMock()
    process.stdout.readline = AsyncMock(
        side_effect=[
            b'{"method":"configWarning","params":{}}\n',
            b'{"id":99,"result":{}}\n',
            b'{"id":1,"result":{"data":[]}}\n',
        ]
    )
    client = CodexConfigurationClient(CodexStdioConnection(process))

    assert asyncio.run(client.request("hooks/list", {"cwds": ["/project"]})) == {
        "data": []
    }
    assert json.loads(process.stdin.write.call_args.args[0]) == {
        "id": 1,
        "method": "hooks/list",
        "params": {"cwds": ["/project"]},
    }


@pytest.mark.parametrize(
    "response", [b"", b'{"id":1,"error":{"message":"write denied"}}\n']
)
def test_client_surfaces_closed_transport_and_rpc_errors(response):
    process = Mock()
    process.stdin.drain = AsyncMock()
    process.stdout.readline = AsyncMock(return_value=response)
    with pytest.raises(RuntimeError):
        client = CodexConfigurationClient(CodexStdioConnection(process))
        asyncio.run(client.request("config/batchWrite", {}))


def test_stalled_approval_is_bounded_and_reaps_its_process(monkeypatch, tmp_path):
    process = Mock(returncode=None)
    process.communicate = AsyncMock(return_value=(b"", b""))
    monkeypatch.setattr(
        approve.asyncio, "create_subprocess_exec", AsyncMock(return_value=process)
    )
    monkeypatch.setattr(approve, "approval_timeout_seconds", 0.01)

    async def stall_initialization(self):
        await asyncio.Event().wait()

    monkeypatch.setattr(CodexConfigurationClient, "initialize", stall_initialization)
    with pytest.raises(TimeoutError):
        asyncio.run(
            approve.approve_launch_hooks(
                "codex", HookDiscoveryRequest(tmp_path, (), False)
            )
        )
    process.kill.assert_called_once()
    process.communicate.assert_awaited_once()
