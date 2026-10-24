import signal

import pytest

import review_changes_cli


@pytest.fixture
def restored_signal_handlers():
    original_handlers = {
        terminating_signal: signal.getsignal(terminating_signal)
        for terminating_signal in (signal.SIGHUP, signal.SIGTERM)
    }
    yield
    for terminating_signal, handler in original_handlers.items():
        signal.signal(terminating_signal, handler)


@pytest.mark.parametrize("terminating_signal", [signal.SIGHUP, signal.SIGTERM])
def test_closing_the_review_pane_unwinds_through_cleanup(
    restored_signal_handlers, terminating_signal
):
    review_changes_cli.route_terminating_signals_through_cleanup()
    handler = signal.getsignal(terminating_signal)
    with pytest.raises(SystemExit) as exit_information:
        handler(terminating_signal, None)
    assert exit_information.value.code == 128 + terminating_signal


def test_signals_after_the_first_cannot_interrupt_cleanup(restored_signal_handlers):
    review_changes_cli.route_terminating_signals_through_cleanup()
    with pytest.raises(SystemExit):
        signal.getsignal(signal.SIGHUP)(signal.SIGHUP, None)
    assert signal.getsignal(signal.SIGHUP) is signal.SIG_IGN
    assert signal.getsignal(signal.SIGTERM) is signal.SIG_IGN
