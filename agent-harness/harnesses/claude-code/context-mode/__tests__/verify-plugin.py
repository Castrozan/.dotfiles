import asyncio
import json
import os
import shlex
import sqlite3
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def run_hook(configuration, event, payload, environment, workspace):
    hook = configuration["hooks"][event][0]["hooks"][0]
    result = subprocess.run(
        shlex.split(hook["command"]),
        input=json.dumps({**payload, "hook_event_name": event}),
        text=True,
        capture_output=True,
        env=environment,
        cwd=workspace,
        timeout=30,
        check=True,
    )
    return json.loads(result.stdout) if result.stdout.strip() else {}


async def verify_plugin(plugin_directory):
    manifest = json.loads((plugin_directory / ".claude-plugin/plugin.json").read_text())
    configuration = json.loads((plugin_directory / "hooks/hooks.json").read_text())
    assert set(configuration["hooks"]) == {
        "SessionStart",
        "PreToolUse",
        "PostToolUse",
        "UserPromptSubmit",
        "PreCompact",
        "Stop",
    }
    with TemporaryDirectory(prefix="context-mode-check-") as temporary_directory:
        root = Path(temporary_directory)
        workspace = root / "project with spaces"
        workspace.mkdir()
        fixture = workspace / "incident.json"
        fixture.write_text(json.dumps({"service": "checkout", "errors": 37}))
        environment = {
            **os.environ,
            "HOME": str(root / "home"),
            "XDG_STATE_HOME": str(root / "state"),
            "CLAUDE_PROJECT_DIR": str(workspace),
            "CLAUDE_PLUGIN_ROOT": str(plugin_directory),
        }
        session_id = "a232f91a-4076-4c6e-8e35-91a7da6d221d"
        payload = {"session_id": session_id, "cwd": str(workspace)}
        startup = run_hook(
            configuration,
            "SessionStart",
            {**payload, "source": "startup"},
            environment,
            workspace,
        )
        routing = startup["hookSpecificOutput"]["additionalContext"]
        assert "ctx_execute" in routing
        decision = run_hook(
            configuration,
            "PreToolUse",
            {
                **payload,
                "tool_name": "Bash",
                "tool_input": {"command": "cat incident.json"},
            },
            environment,
            workspace,
        )
        assert "ctx_execute" in json.dumps(decision), decision
        run_hook(
            configuration,
            "PostToolUse",
            {
                **payload,
                "tool_name": "Read",
                "tool_input": {"file_path": str(fixture)},
                "tool_response": {"content": fixture.read_text()},
            },
            environment,
            workspace,
        )
        run_hook(
            configuration,
            "UserPromptSubmit",
            {**payload, "prompt": "Use PostgreSQL for the checkout ledger."},
            environment,
            workspace,
        )
        run_hook(configuration, "PreCompact", payload, environment, workspace)
        restored = run_hook(
            configuration,
            "SessionStart",
            {**payload, "source": "compact"},
            environment,
            workspace,
        )
        assert "ctx_execute" in restored["hookSpecificOutput"]["additionalContext"]
        run_hook(configuration, "Stop", payload, environment, workspace)

        server = manifest["mcpServers"]["context-mode"]
        parameters = StdioServerParameters(
            **server, env=environment, cwd=str(workspace)
        )
        async with asyncio.timeout(45), stdio_client(parameters) as streams:
            async with ClientSession(*streams) as session:
                initialization = await session.initialize()
                assert initialization.serverInfo.version == manifest["version"]
                tools = {tool.name for tool in (await session.list_tools()).tools}
                assert len(tools) == 11, tools
                result = await session.call_tool(
                    "ctx_execute_file",
                    {
                        "path": str(fixture),
                        "language": "javascript",
                        "code": "console.log(JSON.parse(FILE_CONTENT).errors)",
                    },
                )
                assert not result.isError, result
                assert "37" in "\n".join(
                    getattr(item, "text", "") for item in result.content
                )
                result = await session.call_tool(
                    "ctx_index", {"path": str(fixture), "source": "checkout-incident"}
                )
                assert not result.isError, result

        async with asyncio.timeout(30), stdio_client(parameters) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                result = await session.call_tool(
                    "ctx_search",
                    {"queries": ["checkout"], "source": "checkout-incident"},
                )
                assert not result.isError, result
                assert "37" in "\n".join(
                    getattr(item, "text", "") for item in result.content
                )

        state = root / "state/context-mode"
        session_databases = list((state / "data/sessions").glob("*.db"))
        assert session_databases, list(state.rglob("*"))
        captured = []
        for database in session_databases:
            with sqlite3.connect(database) as connection:
                captured.extend(connection.iterdump())
        assert "incident.json" in "\n".join(captured)
        assert not (root / "home/.claude").exists()
        assert not list(state.rglob("hook-errors.log"))
        assert state.stat().st_mode & 0o077 == 0
        print(
            "Verified six hooks, routing, session capture, compaction, 11 MCP tools, workspace access and persistent search"
        )


if __name__ == "__main__":
    asyncio.run(verify_plugin(Path(sys.argv[1])))
