import sys
from pathlib import Path

PERFORMANCE_SAMPLER_SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(PERFORMANCE_SAMPLER_SCRIPTS_DIRECTORY))

import ai_fleet_metrics
import browser_metrics
import input_layer_metrics
import multiplexer_metrics


def test_classify_fleet_bucket_matches_substring_and_basename():
    assert (
        ai_fleet_metrics.classify_fleet_bucket("/nix/store/x/bin/claude --resume")
        == "claude_cli"
    )
    assert (
        ai_fleet_metrics.classify_fleet_bucket("node /x/chrome-devtools-mcp/index.js")
        == "chrome_devtools_mcp"
    )
    assert ai_fleet_metrics.classify_fleet_bucket("opencode") == "opencode"
    assert ai_fleet_metrics.classify_fleet_bucket("/usr/bin/login") is None


def test_classify_fleet_bucket_excludes_tmux_wrapped_opencode():
    tmux_wrapper_command = (
        "tmux -L jarvis new-session -d -s jarvis bash -lc 'exec opencode'"
    )
    assert ai_fleet_metrics.classify_fleet_bucket(tmux_wrapper_command) is None


def test_parse_fleet_process_table_counts_and_sums_rss():
    ps_output = "\n".join(
        [
            "101 2000 /nix/store/x/bin/claude --agent-name foo",
            "102 500 node /x/chrome-devtools-mcp/index.js",
            "103 700 node /x/chrome-devtools-mcp/index.js",
            "104 900 opencode",
        ]
    )
    parsed = ai_fleet_metrics.parse_fleet_process_table(ps_output)
    assert parsed["counts"] == {
        "claude_cli": 1,
        "chrome_devtools_mcp": 2,
        "opencode": 1,
    }
    assert parsed["rss_kilobytes"]["opencode"] == 900


def test_parse_claude_fanout_counts_children_per_session():
    ps_output = "\n".join(
        [
            "101 1 /nix/store/x/bin/claude session-a",
            "201 101 node mcp-one",
            "202 101 node mcp-two",
            "301 1 /usr/bin/other",
        ]
    )
    fanout = ai_fleet_metrics.parse_claude_fanout(ps_output)
    assert fanout == {"sessions": 1, "mean": 2.0, "max": 2}


def test_parse_claude_session_kinds_splits_agent_and_interactive():
    ps_output = "\n".join(
        [
            "/nix/store/x/bin/claude --agent-name steward",
            "/nix/store/x/bin/claude --resume",
            "/usr/bin/notclaude",
        ]
    )
    kinds = ai_fleet_metrics.parse_claude_session_kinds(ps_output)
    assert kinds == {"agents": 1, "interactive": 1}


def test_parse_browser_total_rss_sums_per_browser():
    ps_output = "\n".join(
        [
            "5000 /Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "400 /Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    )
    assert browser_metrics.parse_browser_total_rss(ps_output) == {
        "brave": 5000,
        "chrome": 400,
    }


def test_parse_brave_renderer_breakdown_separates_extension_renderers():
    ps_output = "\n".join(
        [
            "1024 /x/Brave Browser Helper (Renderer).app/Contents/MacOS/Brave Browser Helper (Renderer) --type=renderer",
            "2048 /x/Brave Browser Helper (Renderer) --type=renderer --extension-process",
        ]
    )
    breakdown = browser_metrics.parse_brave_renderer_breakdown(ps_output)
    assert breakdown["renderers"] == 2
    assert breakdown["renderer_megabytes"] == 3.0
    assert breakdown["extension_renderers"] == 1
    assert breakdown["extension_megabytes"] == 2.0


def test_parse_long_lived_brave_renderer_count_requires_day_marker():
    ps_output = "\n".join(
        [
            "1-02:03:04 /x/Brave Browser Helper (Renderer)",
            "05:06 /x/Brave Browser Helper (Renderer)",
            "2-00:00:00 /x/some other process",
        ]
    )
    assert browser_metrics.parse_long_lived_brave_renderer_count(ps_output) == 1


def test_find_herdr_server_pid_matches_server_argument():
    ps_output = "\n".join(
        [
            "501 /nix/store/x/bin/herdr server",
            "502 herdr",
            "503 /nix/store/x/bin/herderd server",
        ]
    )
    assert multiplexer_metrics.find_herdr_server_pid(ps_output) == "501"


def test_parse_herdr_topology_sums_tabs_and_panes():
    workspace_list_json = '{"result":{"workspaces":[{"tab_count":3,"pane_count":4},{"tab_count":1,"pane_count":2}]}}'
    topology = multiplexer_metrics.parse_herdr_topology(workspace_list_json)
    assert topology == {"workspaces": 2, "tabs": 4, "panes": 6}


def test_parse_elapsed_time_to_seconds_handles_days_and_short_forms():
    assert input_layer_metrics.parse_elapsed_time_to_seconds("1-02:03:04") == 93784
    assert input_layer_metrics.parse_elapsed_time_to_seconds("05:06") == 306
    assert input_layer_metrics.parse_elapsed_time_to_seconds("12:34:56") == 45296
