import json
import subprocess
import threading
import time

from wake_phrase import LiveSession

PEER_TIMEOUT_SECONDS = 10
PEER_REFRESH_SECONDS = 60
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


def sessions_everywhere(local_sessions, peer_sessions):
    local_servants = {session.servant for session in local_sessions}
    return [
        *local_sessions,
        *(
            session
            for session in peer_sessions
            if session.servant not in local_servants
        ),
    ]


def start_daemon_thread(work):
    threading.Thread(target=work, daemon=True).start()


class PeerSessions:
    def __init__(
        self,
        peer_hosts,
        run,
        clock=time.monotonic,
        start_worker=start_daemon_thread,
    ):
        self.peer_hosts = peer_hosts
        self.run = run
        self.clock = clock
        self.start_worker = start_worker
        self.sessions = []
        self.started_at = None
        self.refreshing = False
        self.lock = threading.Lock()

    def known(self):
        if self.refresh_is_due():
            self.start_worker(self.refresh)
        return self.sessions

    def refresh_is_due(self):
        if not self.peer_hosts:
            return False
        with self.lock:
            if self.refreshing or self.started_within_the_interval():
                return False
            self.refreshing = True
            self.started_at = self.clock()
            return True

    def started_within_the_interval(self):
        return (
            self.started_at is not None
            and self.clock() - self.started_at < PEER_REFRESH_SECONDS
        )

    def refresh(self):
        try:
            self.sessions = [
                session
                for host in self.peer_hosts
                for session in sessions_of_peer(host, self.run)
            ]
        finally:
            self.refreshing = False
