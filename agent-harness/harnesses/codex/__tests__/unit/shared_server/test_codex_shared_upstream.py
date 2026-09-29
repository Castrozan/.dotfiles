import asyncio
from uuid import uuid4

from codex_client_context import ClientContext
from codex_upstream import Upstream


def test_resume_resolves_shell_policy_from_the_saved_workspace(tmp_path):
    async def exercise():
        context = ClientContext(tmp_path / "context", {})
        upstream = Upstream(None)
        identifier = str(uuid4())
        requests = []

        async def request(method, parameters):
            requests.append((method, parameters))
            if method == "thread/loaded/list":
                return {"data": []}
            if method == "thread/read":
                return {"thread": {"cwd": "/saved/workspace"}}
            return {"config": {"shell_environment_policy": {"exclude": ["SECRET*"]}}}

        upstream.request = request
        try:
            prepared = await upstream.prepare(
                {"method": "thread/resume", "params": {"threadId": identifier}},
                context,
                "/launch/workspace",
            )
            assert prepared.working_directory == "/saved/workspace"
            assert requests[-1] == (
                "config/read",
                {"cwd": "/saved/workspace", "includeLayers": False},
            )
            assert prepared.configuration["shell_environment_policy"]["exclude"] == [
                "SECRET*"
            ]
        finally:
            context.close()

    asyncio.run(exercise())
