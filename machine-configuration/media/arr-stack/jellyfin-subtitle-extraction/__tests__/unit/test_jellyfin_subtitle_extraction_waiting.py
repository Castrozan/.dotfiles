import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jellyfin_subtitle_extraction_test_doubles import (
    JELLYFIN_BASE_URL,
    WATCHING_SESSIONS,
    install_warmer_environment,
    main_module,
)


def test_waiting_needs_two_quiet_polls_so_an_autoplay_gap_is_not_mistaken_for_idle(
    monkeypatch,
):
    session_reads = [WATCHING_SESSIONS, [], WATCHING_SESSIONS, [], []]
    slept_seconds = []
    monkeypatch.setattr(
        main_module, "list_active_sessions", lambda *_: session_reads.pop(0)
    )
    monkeypatch.setattr(main_module.time, "sleep", slept_seconds.append)
    assert main_module.wait_for_a_quiet_server(JELLYFIN_BASE_URL, "key", 30, 1200)
    assert slept_seconds == [30, 30, 30, 30]


def test_waiting_gives_up_once_its_deadline_passes(monkeypatch):
    monkeypatch.setattr(
        main_module, "list_active_sessions", lambda *_: WATCHING_SESSIONS
    )
    monkeypatch.setattr(main_module.time, "sleep", lambda _: None)
    assert not main_module.wait_for_a_quiet_server(JELLYFIN_BASE_URL, "key", 30, 60)


def test_jellyfin_going_away_mid_run_ends_the_sweep_without_a_traceback(
    monkeypatch, capsys
):
    install_warmer_environment(monkeypatch)

    def jellyfin_went_away(*_):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(main_module, "list_active_sessions", jellyfin_went_away)
    main_module.main()
    assert "jellyfin stopped answering" in capsys.readouterr().out
