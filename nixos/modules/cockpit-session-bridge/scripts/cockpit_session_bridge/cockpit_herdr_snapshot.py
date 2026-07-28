import json

from cockpit_multiplexer_port import (
    CockpitMultiplexerSession,
    CockpitMultiplexerWindow,
)


def parse_herdr_runtime_snapshot(snapshot_output):
    snapshot = _decode_snapshot_payload(snapshot_output)
    agent_by_tab_identifier = {
        agent.get("tab_id"): agent.get("agent", "")
        for agent in snapshot.get("agents", [])
    }
    terminal_by_tab_identifier = {}
    for pane in snapshot.get("panes", []):
        terminal_by_tab_identifier.setdefault(
            pane.get("tab_id"), pane.get("terminal_id", "")
        )
    tabs_by_workspace_identifier = {}
    for tab in snapshot.get("tabs", []):
        tabs_by_workspace_identifier.setdefault(tab.get("workspace_id"), []).append(
            CockpitMultiplexerWindow(
                window_identifier=tab.get("tab_id", ""),
                window_title=tab.get("label", ""),
                agent_driver=agent_by_tab_identifier.get(tab.get("tab_id"), ""),
                terminal_identifier=terminal_by_tab_identifier.get(
                    tab.get("tab_id"), ""
                ),
            )
        )
    return [
        CockpitMultiplexerSession(
            session_name=workspace.get("label", ""),
            windows=tuple(
                tabs_by_workspace_identifier.get(workspace.get("workspace_id"), [])
            ),
        )
        for workspace in snapshot.get("workspaces", [])
    ]


def parse_herdr_workspace_identifiers(snapshot_output):
    snapshot = _decode_snapshot_payload(snapshot_output)
    workspace_identifier_by_label = {}
    for workspace in snapshot.get("workspaces", []):
        workspace_identifier_by_label.setdefault(
            workspace.get("label", ""), workspace.get("workspace_id", "")
        )
    return workspace_identifier_by_label


def _decode_snapshot_payload(snapshot_output):
    try:
        decoded_reply = json.loads(snapshot_output)
    except (ValueError, TypeError):
        return {}
    if not isinstance(decoded_reply, dict):
        return {}
    return decoded_reply.get("result", {}).get("snapshot", {})
