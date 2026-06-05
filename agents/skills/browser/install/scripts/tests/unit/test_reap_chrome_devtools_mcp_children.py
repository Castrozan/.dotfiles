from reap_chrome_devtools_mcp_children import (
    parse_elapsed_time_to_seconds,
    select_reapable_chrome_devtools_mcp_child_process_ids,
)

SUPERGATEWAY_BRIDGE_LINE = (
    "1540 01-00:40:05 /nix/store/abc-nodejs/bin/node "
    "/nix/store/def-supergateway/lib/node_modules/supergateway/dist/index.js "
    "--stdio /nix/store/ghi-chrome-devtools-mcp-1.1.1/bin/chrome-devtools-mcp "
    "--autoConnect --outputTransport streamableHttp --port 8767"
)
CHROME_DEVTOOLS_MCP_CHILD_LINE_OLD = (
    "39723 01-12:21 /nix/store/abc-nodejs/bin/node "
    "/nix/store/ghi-chrome-devtools-mcp-1.1.1/bin/chrome-devtools-mcp "
    "--autoConnect --userDataDir /Users/lucas/Library/Application Support/Google/Chrome"
)
CHROME_DEVTOOLS_MCP_CHILD_LINE_RECENT = (
    "44536 04:27 /nix/store/abc-nodejs/bin/node "
    "/nix/store/ghi-chrome-devtools-mcp-1.1.1/bin/chrome-devtools-mcp "
    "--autoConnect --userDataDir /Users/lucas/Library/Application Support/Google/Chrome"
)
UNRELATED_PROCESS_LINE = (
    "861 10-00:00:00 /Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)


def test_parses_minutes_and_seconds():
    assert parse_elapsed_time_to_seconds("33:34") == 33 * 60 + 34


def test_parses_hours_minutes_seconds():
    assert parse_elapsed_time_to_seconds("01:12:21") == 3600 + 12 * 60 + 21


def test_parses_days_hours_minutes_seconds():
    assert parse_elapsed_time_to_seconds("01-00:40:05") == 86400 + 40 * 60 + 5


def test_never_selects_the_supergateway_bridge_itself():
    selected = select_reapable_chrome_devtools_mcp_child_process_ids(
        SUPERGATEWAY_BRIDGE_LINE, own_process_id=999, minimum_age_seconds=0
    )
    assert selected == []


def test_selects_all_children_at_zero_age_threshold():
    process_status_output = "\n".join(
        [
            SUPERGATEWAY_BRIDGE_LINE,
            CHROME_DEVTOOLS_MCP_CHILD_LINE_OLD,
            CHROME_DEVTOOLS_MCP_CHILD_LINE_RECENT,
            UNRELATED_PROCESS_LINE,
        ]
    )
    selected = select_reapable_chrome_devtools_mcp_child_process_ids(
        process_status_output, own_process_id=999, minimum_age_seconds=0
    )
    assert selected == [39723, 44536]


def test_age_threshold_spares_recent_children_and_reaps_stale_ones():
    process_status_output = "\n".join(
        [CHROME_DEVTOOLS_MCP_CHILD_LINE_OLD, CHROME_DEVTOOLS_MCP_CHILD_LINE_RECENT]
    )
    selected = select_reapable_chrome_devtools_mcp_child_process_ids(
        process_status_output, own_process_id=999, minimum_age_seconds=3600
    )
    assert selected == [39723]


def test_excludes_own_process_id():
    selected = select_reapable_chrome_devtools_mcp_child_process_ids(
        CHROME_DEVTOOLS_MCP_CHILD_LINE_OLD, own_process_id=39723, minimum_age_seconds=0
    )
    assert selected == []


def test_ignores_unrelated_processes():
    selected = select_reapable_chrome_devtools_mcp_child_process_ids(
        UNRELATED_PROCESS_LINE, own_process_id=999, minimum_age_seconds=0
    )
    assert selected == []
