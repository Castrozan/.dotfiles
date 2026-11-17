import json
import subprocess
from concurrent.futures import ThreadPoolExecutor

from wake_phrase import LiveSession

PEER_TIMEOUT_SECONDS = 10
REACH_PEER = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5"]
PEER_UNREADABLE = (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError)


def listing_of(sessions):
    return json.dumps(
        [{"servant": session.servant, "pane": session.pane} for session in sessions]
    )


def sessions_of_peer(host, run):
    try:
        listing = run(
            [*REACH_PEER, host, "avatar-wake", "--sessions"],
            capture_output=True,
            text=True,
            timeout=PEER_TIMEOUT_SECONDS,
        )
        if listing.returncode != 0:
            return []
        return [
            LiveSession(entry["servant"], entry["pane"], host)
            for entry in json.loads(listing.stdout)
        ]
    except PEER_UNREADABLE:
        return []


def sessions_everywhere(local_sessions, peer_hosts, run):
    sessions = list(local_sessions)
    if not peer_hosts:
        return sessions
    local_servants = {session.servant for session in sessions}
    with ThreadPoolExecutor(max_workers=len(peer_hosts)) as executor:
        listings = executor.map(lambda host: sessions_of_peer(host, run), peer_hosts)
        for listing in listings:
            sessions.extend(
                session for session in listing if session.servant not in local_servants
            )
    return sessions
