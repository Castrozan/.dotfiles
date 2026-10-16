"""Join allowlisted A2A and Herdr metadata by structural identity."""

from .validation import label

STATES = {"idle", "working", "blocked", "done", "unknown"}
COLLECTIONS = ("agents", "panes", "tabs", "workspaces", "layouts")


def snapshot_from(reply):
    if not isinstance(reply, dict):
        raise ValueError("expected Herdr snapshot object")
    result = reply.get("result")
    snapshot = result.get("snapshot") if isinstance(result, dict) else None
    validate_snapshot_header(snapshot)
    if any(not isinstance(snapshot.get(key), list) for key in COLLECTIONS):
        raise ValueError("incomplete Herdr snapshot collections")
    return snapshot


def validate_snapshot_header(snapshot):
    if not isinstance(snapshot, dict):
        raise ValueError("missing Herdr snapshot version/protocol")
    if not isinstance(snapshot.get("version"), str):
        raise ValueError("missing Herdr snapshot version/protocol")
    if not isinstance(snapshot.get("protocol"), int):
        raise ValueError("missing Herdr snapshot version/protocol")


def peer_names(directory):
    if not isinstance(directory, dict):
        raise ValueError("expected A2A directory object")
    peers = {}
    for peer in directory.values():
        add_peer(peers, peer)
    return peers


def add_peer(peers, peer):
    if not isinstance(peer, dict):
        raise ValueError("invalid A2A peer")
    pane = label(peer.get("paneId"), "paneId")
    if pane in peers:
        raise ValueError("duplicate A2A pane identity")
    peers[pane] = label(peer.get("name"), "peer name")


def session_id(agent):
    identity = agent.get("agent_session") or {}
    if not isinstance(identity, dict):
        raise ValueError("invalid Herdr session reference")
    # Path references are deliberately neither retained nor opened.
    if identity.get("kind") == "id":
        return label(identity.get("value"), "session ID")
    return None


def blockers(session, state):
    result = []
    if not session:
        result.append("session_identity_unavailable")
    if state == "blocked":
        result.append("agent_requires_input")
    return result


def normalized_agent(agent, peers):
    if not isinstance(agent, dict):
        raise ValueError("invalid Herdr agent")
    pane = label(agent.get("pane_id"), "pane_id")
    session = session_id(agent)
    state = agent.get("agent_status", "unknown")
    if state not in STATES:
        raise ValueError("unknown Herdr agent status")
    return {
        "pane_id": pane,
        "session_id": session,
        "agent_id": pane,
        "name": peers.get(pane) or agent.get("name"),
        "harness": agent.get("agent"),
        "tab_id": agent.get("tab_id"),
        "workspace_id": agent.get("workspace_id"),
        "state": state,
        "interactive_ready": agent.get("interactive_ready") is True,
        "launch_pending": agent.get("launch_pending", False) is not False,
        "delivery_readiness": "unverified",
        "capabilities": ["a2a.dispatch", "a2a.status"] if pane in peers else [],
        "blockers": blockers(session, state),
    }


def normalize(directory, reply):
    peers = peer_names(directory)
    snapshot = snapshot_from(reply)
    rows = [normalized_agent(agent, peers) for agent in snapshot["agents"]]
    panes = [row["pane_id"] for row in rows]
    if len(set(panes)) != len(panes):
        raise ValueError("duplicate Herdr pane identity")
    if set(peers) - set(panes):
        raise ValueError("A2A and Herdr inventories disagree; refresh again")
    return rows
