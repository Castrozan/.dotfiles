from a2a_cli import peer_identity
from wake_phrase import LiveSession


def live_sessions():
    sessions = []
    for pane in peer_identity.read_live_panes():
        servant = peer_identity.identity_of_pane(pane).get("servant")
        if servant:
            sessions.append(LiveSession(servant=servant, pane=pane["pane_id"]))
    return sessions
