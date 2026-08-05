def test_application_keeps_running_while_its_window_is_still_open(daemon):
    history = daemon.ApplicationWindowHistory(
        first_seen_at=0.0, last_seen_with_a_window_at=100.0
    )

    assert not daemon.should_request_quit(history, 100.0)


def test_application_is_quit_once_its_last_window_closes(daemon):
    history = daemon.ApplicationWindowHistory(
        first_seen_at=0.0, last_seen_with_a_window_at=100.0
    )
    still_within_grace = 100.0 + daemon.SECONDS_WITHOUT_A_WINDOW_BEFORE_QUITTING - 1
    past_grace = 100.0 + daemon.SECONDS_WITHOUT_A_WINDOW_BEFORE_QUITTING

    assert not daemon.should_request_quit(history, still_within_grace)
    assert daemon.should_request_quit(history, past_grace)


def test_application_that_never_opened_a_window_is_still_quit(daemon):
    history = daemon.ApplicationWindowHistory(first_seen_at=0.0)
    launch_grace = daemon.SECONDS_AFTER_LAUNCH_BEFORE_QUITTING_AN_APPLICATION_THAT_NEVER_OPENED_A_WINDOW

    assert not daemon.should_request_quit(history, launch_grace - 1)
    assert daemon.should_request_quit(history, launch_grace)


def test_quit_is_requested_again_when_the_application_ignores_the_first_request(daemon):
    history = daemon.ApplicationWindowHistory(
        first_seen_at=0.0, last_seen_with_a_window_at=100.0, quit_requested_at=110.0
    )
    repeat_interval = daemon.SECONDS_BETWEEN_REPEATED_QUIT_REQUESTS

    assert not daemon.should_request_quit(history, 110.0 + repeat_interval - 1)
    assert daemon.should_request_quit(history, 110.0 + repeat_interval)
