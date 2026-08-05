import json


def test_the_isolated_claude_json_keeps_the_session_state_written_into_it(run_seed):
    invoke, isolated = run_seed
    assert invoke().returncode == 0
    isolated_claude_json = isolated / ".claude.json"
    assert json.loads(isolated_claude_json.read_text())["installMethod"] == "shared"

    live_config = json.loads(isolated_claude_json.read_text())
    live_config["installMethod"] = "edited-at-runtime"
    isolated_claude_json.write_text(json.dumps(live_config))

    assert invoke().returncode == 0
    assert (
        json.loads(isolated_claude_json.read_text())["installMethod"]
        == "edited-at-runtime"
    ), "the isolated .claude.json holds live session state and must not be reseeded"


def test_mcp_servers_added_to_the_shared_config_reach_the_isolated_config(
    run_seed, shared_config_directory
):
    invoke, isolated = run_seed
    assert invoke().returncode == 0

    shared_claude_json = shared_config_directory.parent / ".claude.json"
    shared_config = json.loads(shared_claude_json.read_text())
    shared_config["mcpServers"]["codex"] = {"command": "codex"}
    shared_claude_json.write_text(json.dumps(shared_config))

    assert invoke().returncode == 0
    isolated_config = json.loads((isolated / ".claude.json").read_text())
    assert isolated_config["mcpServers"]["codex"] == {"command": "codex"}


def test_a_shared_mcp_server_whose_command_changed_is_refreshed(
    run_seed, shared_config_directory
):
    invoke, isolated = run_seed
    assert invoke().returncode == 0

    shared_claude_json = shared_config_directory.parent / ".claude.json"
    shared_config = json.loads(shared_claude_json.read_text())
    shared_config["mcpServers"]["chrome-devtools"] = {"command": "patched-mcp"}
    shared_claude_json.write_text(json.dumps(shared_config))

    assert invoke().returncode == 0
    isolated_config = json.loads((isolated / ".claude.json").read_text())
    assert isolated_config["mcpServers"]["chrome-devtools"] == {
        "command": "patched-mcp"
    }


def test_an_mcp_server_added_inside_the_isolated_config_survives_a_reseed(run_seed):
    invoke, isolated = run_seed
    assert invoke().returncode == 0

    isolated_claude_json = isolated / ".claude.json"
    isolated_config = json.loads(isolated_claude_json.read_text())
    isolated_config["mcpServers"]["work-only"] = {"command": "work-mcp"}
    isolated_claude_json.write_text(json.dumps(isolated_config))

    assert invoke().returncode == 0
    reseeded = json.loads(isolated_claude_json.read_text())
    assert reseeded["mcpServers"]["work-only"] == {"command": "work-mcp"}
    assert "chrome-devtools" in reseeded["mcpServers"]
