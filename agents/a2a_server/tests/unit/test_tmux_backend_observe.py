import re

from a2a_server.backends.tmux_backend import TmuxAttachedAgentBackend


def _replace_capture_pane_text_with(backend, text):
    backend._capture_pane_text = lambda: text


def _set_target_window_exists_to(backend, exists):
    backend._target_tmux_window_exists = lambda: exists


class TestObserveProducesActivityOnlyForNewMeaningfulLines:
    def test_first_observation_after_start_reports_no_new_lines_when_pane_unchanged(
        self,
    ):
        pattern = re.compile(r"^⏺ ")
        backend = TmuxAttachedAgentBackend("s", "w", meaningful_line_pattern=pattern)
        _replace_capture_pane_text_with(backend, "⏺ first response\n")
        _set_target_window_exists_to(backend, True)
        backend.start()
        observation = backend.observe()
        assert observation.raw_output_since_last_call == ""
        assert observation.is_alive is True

    def test_observation_reports_only_newly_appeared_meaningful_lines(self):
        pattern = re.compile(r"^⏺ ")
        backend = TmuxAttachedAgentBackend("s", "w", meaningful_line_pattern=pattern)
        _replace_capture_pane_text_with(backend, "⏺ first response\n")
        _set_target_window_exists_to(backend, True)
        backend.start()
        _replace_capture_pane_text_with(
            backend, "⏺ first response\n⏺ second response\n"
        )
        observation = backend.observe()
        assert observation.raw_output_since_last_call == "⏺ second response"

    def test_observation_ignores_noise_lines_that_change_between_captures(self):
        pattern = re.compile(r"^⏺ ")
        backend = TmuxAttachedAgentBackend("s", "w", meaningful_line_pattern=pattern)
        first_capture = "⏺ first response\n  Haiku 4.5 │ ctx 20% │ lim 19% 3h17m\n"
        second_capture = "⏺ first response\n  Haiku 4.5 │ ctx 21% │ lim 19% 3h16m\n"
        _replace_capture_pane_text_with(backend, first_capture)
        _set_target_window_exists_to(backend, True)
        backend.start()
        _replace_capture_pane_text_with(backend, second_capture)
        observation = backend.observe()
        assert observation.raw_output_since_last_call == ""

    def test_observation_reports_repeated_response_as_new_when_occurrence_count_grows(
        self,
    ):
        pattern = re.compile(r"^⏺ ")
        backend = TmuxAttachedAgentBackend("s", "w", meaningful_line_pattern=pattern)
        _replace_capture_pane_text_with(backend, "⏺ Hi\n")
        _set_target_window_exists_to(backend, True)
        backend.start()
        _replace_capture_pane_text_with(backend, "⏺ Hi\n⏺ Hi\n")
        observation = backend.observe()
        assert observation.raw_output_since_last_call == "⏺ Hi"

    def test_observation_refreshes_activity_timestamp_when_new_occurrence_appears(self):
        pattern = re.compile(r"^⏺ ")
        backend = TmuxAttachedAgentBackend("s", "w", meaningful_line_pattern=pattern)
        _replace_capture_pane_text_with(backend, "⏺ Hi\n")
        _set_target_window_exists_to(backend, True)
        backend.start()
        activity_after_start = backend._last_activity_at_epoch_seconds
        _replace_capture_pane_text_with(backend, "⏺ Hi\n⏺ Hi\n")
        observation = backend.observe()
        assert observation.last_activity_at_epoch_seconds >= activity_after_start

    def test_observation_reports_target_not_alive_when_window_disappears(self):
        backend = TmuxAttachedAgentBackend("s", "w", meaningful_line_pattern=None)
        _replace_capture_pane_text_with(backend, "initial\n")
        _set_target_window_exists_to(backend, True)
        backend.start()
        _set_target_window_exists_to(backend, False)
        observation = backend.observe()
        assert observation.is_alive is False
