import json
import sys
import tempfile
import time
from pathlib import Path

from native_model_server import native_model_server
from native_opencode_profile import prepare_profile
from native_opencode_server import native_server
from unit.hook_bridge_test_support import (
    write_hook_bridge_sources,
    write_hook_dispatcher_launcher,
)


def main():
    executable = Path(sys.argv[1])
    sources = Path(sys.argv[2])
    with tempfile.TemporaryDirectory(prefix="opencode-v2-hooks-") as temporary:
        root = Path(temporary)
        bridge = root / "bridge"
        bridge.mkdir()
        record = root / "dispatch.json"
        write_hook_bridge_sources(bridge, write_hook_dispatcher_launcher(bridge))
        with native_model_server() as model:
            environment, workspace = prepare_profile(
                root / "profile",
                sources,
                model_url=f"http://127.0.0.1:{model.server_port}/v1",
            )
            configuration = Path(environment["OPENCODE_CONFIG_DIR"])
            configuration.chmod(0o755)
            (configuration / "plugins").mkdir()
            (configuration / "plugins/dotfiles-hook-bridge").symlink_to(
                bridge, target_is_directory=True
            )
            configuration.chmod(0o555)
            environment.update(
                {
                    "OPENCODE_HOOK_RECORD": str(record),
                    "OPENCODE_HOOK_RESPONSES": json.dumps(
                        {
                            "session-start-dispatcher.py": {
                                "hookSpecificOutput": {
                                    "additionalContext": "NATIVE_SESSION_CONTEXT"
                                }
                            },
                            "stop-dispatcher.py": {
                                "decision": "block",
                                "reason": "NATIVE_REPLY_CORRECTION",
                            },
                            "pre-tool-use-dispatcher.py": {
                                "hookSpecificOutput": {
                                    "permissionDecision": "deny",
                                    "permissionDecisionReason": "NATIVE_GUARD_DENIAL",
                                }
                            },
                        }
                    ),
                }
            )
            try:
                with native_server(executable, environment, workspace) as server:
                    plugins = server.request("/api/plugin", location=True)["data"]
                    assert any(
                        plugin["id"] == "dotfiles.hook-bridge"
                        and plugin["state"]["status"] == "active"
                        for plugin in plugins
                    ), [
                        plugin
                        for plugin in plugins
                        if plugin["source"]["type"] != "builtin"
                    ]
                    session = server.request(
                        "/api/session",
                        {
                            "title": "Hook acceptance",
                            "agent": "software-engineer",
                            "model": {"providerID": "acceptance", "id": "fixture"},
                            "location": {"directory": str(workspace)},
                        },
                    )["data"]["id"]
                    marker = workspace / "forbidden"
                    server.request(
                        f"/api/session/{session}/prompt",
                        {
                            "text": json.dumps(
                                {
                                    "tool": "shell",
                                    "input": {"command": f"touch {marker}"},
                                }
                            )
                        },
                    )
                    server.request(
                        f"/api/experimental/session/{session}/wait", {}, method="POST"
                    )
                    messages = server.request(f"/api/session/{session}/message")["data"]
                    assert "NATIVE_GUARD_DENIAL" in json.dumps(messages), messages
                    assert not marker.exists()
                    assert any(
                        "NATIVE_SESSION_CONTEXT" in json.dumps(request)
                        for request in model.requests
                    )
                    deadline = time.monotonic() + 5
                    while time.monotonic() < deadline:
                        payloads = json.loads(record.read_text())
                        stops = [
                            item["payload"]
                            for item in payloads
                            if item["dispatcher"] == "stop-dispatcher.py"
                        ]
                        if len(stops) == 2:
                            break
                        time.sleep(0.05)
                    assert len(stops) == 2, payloads
                    assert stops[1]["stop_hook_active"] is True, stops
                    assert any(
                        "NATIVE_REPLY_CORRECTION" in json.dumps(request)
                        for request in model.requests
                    )
                    assert any(
                        item["payload"].get("tool_name") == "Bash" for item in payloads
                    )
                    server.request(f"/api/session/{session}/compact", {})
                    server.request(
                        f"/api/experimental/session/{session}/wait", {}, method="POST"
                    )
                    messages = server.request(f"/api/session/{session}/message")["data"]
                    compactions = [
                        message
                        for message in messages
                        if message["type"] == "compaction"
                    ]
                    assert compactions and compactions[0]["status"] == "completed", (
                        compactions
                    )
                    payloads = json.loads(record.read_text())
                    assert any(
                        item["payload"].get("source") == "compact" for item in payloads
                    ), payloads
            finally:
                for directory in root.rglob("*"):
                    if directory.is_dir() and not directory.is_symlink():
                        directory.chmod(0o755)
    print(
        "Verified V2 plugin load, startup injection, shell denial, bounded reply correction and compaction"
    )


if __name__ == "__main__":
    main()
