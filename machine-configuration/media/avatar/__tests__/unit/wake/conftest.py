from types import SimpleNamespace

import floor_cli
import local_seat
import mac_wake_boundaries
import pytest
import wake_boundaries


@pytest.fixture
def shown(monkeypatch):
    servants = []
    monkeypatch.setattr(
        floor_cli.servant_character,
        "show_for",
        lambda servant: servants.append(servant),
    )
    return servants


@pytest.fixture
def seat_listening(monkeypatch):
    state = SimpleNamespace(listening=True)
    monkeypatch.setattr(local_seat, "conversation_listening", lambda: state.listening)
    return state


@pytest.fixture
def clock():
    return SimpleNamespace(now=100.0)


@pytest.fixture
def on_a_mac(monkeypatch, seat_listening, clock):
    monkeypatch.setattr(wake_boundaries.sys, "platform", "darwin")
    monkeypatch.setenv(mac_wake_boundaries.HOST_ENVIRONMENT_VARIABLE, "kira")
    transcript = mac_wake_boundaries.ConversationTranscript
    monkeypatch.setattr(
        mac_wake_boundaries,
        "ConversationTranscript",
        lambda: transcript(lambda: clock.now),
    )
    return wake_boundaries.for_this_machine()
