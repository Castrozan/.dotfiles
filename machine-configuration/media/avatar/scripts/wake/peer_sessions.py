import dataclasses
import json
import subprocess
import threading
import time

import listener_runtime
from conversation_seat import Seat, open_seat
from servant_panes import live_sessions
from wake_phrase import LiveSession

PEER_TIMEOUT_SECONDS = 10
PEER_REFRESH_SECONDS = 20
REACH_PEER = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5"]
PEER_UNREADABLE = (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError)


@dataclasses.dataclass(frozen=True)
class PeerListing:
    sessions: list
    conversation_seat: str | None


NOTHING_LISTED = PeerListing([], None)


def listing_of(sessions, conversation_seat):
    return json.dumps(
        {
            "sessions": [
                {"servant": session.servant, "pane": session.pane}
                for session in sessions
            ],
            "conversation_seat": conversation_seat,
        }
    )


def this_machine_listing():
    return listing_of(live_sessions(), open_seat(listener_runtime.runtime_directory()))


def sessions_of_peer(host, run):
    try:
        listing = run(
            [*REACH_PEER, host, "avatar-wake", "--sessions"],
            capture_output=True,
            text=True,
            timeout=PEER_TIMEOUT_SECONDS,
        )
        if listing.returncode != 0:
            return NOTHING_LISTED
        payload = json.loads(listing.stdout)
        return PeerListing(
            [
                LiveSession(entry["servant"], entry["pane"], host)
                for entry in payload["sessions"]
            ],
            payload["conversation_seat"],
        )
    except PEER_UNREADABLE:
        return NOTHING_LISTED


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
        self.discord_hosts = []
        self.started_at = None
        self.refreshing = False
        self.lock = threading.Lock()

    def known(self):
        self.refresh_when_due()
        return self.sessions

    def discord_call_host(self):
        self.refresh_when_due()
        return next(iter(self.discord_hosts), None)

    def refresh_when_due(self):
        if self.refresh_is_due():
            self.start_worker(self.refresh)

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
            listings = {
                host: sessions_of_peer(host, self.run) for host in self.peer_hosts
            }
            self.sessions = [
                session for listing in listings.values() for session in listing.sessions
            ]
            self.discord_hosts = [
                host
                for host, listing in listings.items()
                if listing.conversation_seat == Seat.DISCORD
            ]
        finally:
            self.refreshing = False
