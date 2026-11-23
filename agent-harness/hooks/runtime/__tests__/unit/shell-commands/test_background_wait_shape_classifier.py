import itertools

import background_wait_shape_classifier as sut
import pytest

INCIDENT_PEER_REPORT_POLL = (
    "first=$(orchestrator heartbeat show Reviewer-w4E-p6 2>/dev/null | head -1); n=0; "
    'until { cur=$(orchestrator heartbeat show Reviewer-w4E-p6 2>/dev/null | head -1); [ "$cur" != "$first" ] '
    '&& echo "$cur" | grep -qE "· (done|blocked) · "; } || [ $n -ge 240 ]; '
    "do sleep 45; n=$((n+1)); done; orchestrator heartbeat show Reviewer-w4E-p6"
)

INCIDENT_POLL_WITH_PANE_LIVENESS_EXIT = (
    "first=$(orchestrator heartbeat show Reviewer-w4E-p6 2>/dev/null | head -1); n=0; "
    'until { cur=$(orchestrator heartbeat show Reviewer-w4E-p6 2>/dev/null | head -1); [ "$cur" != "$first" ]; } '
    "|| ! herdr pane get w4E:p6 >/dev/null 2>&1 || [ $n -ge 240 ]; "
    "do sleep 45; n=$((n+1)); done; "
    'herdr pane get w4E:p6 >/dev/null 2>&1 || echo "PEER-GONE: pane w4E:p6 closed"; '
    "orchestrator heartbeat show Reviewer-w4E-p6"
)

PEER_STATE_READS = (
    "orchestrator heartbeat show Reviewer-w4E-p6",
    "orchestrator status",
    "herdr agent read w4E:p6 --source visible",
    "herdr pane read w4E:p6 --lines 40",
    "a2a status reviewer 7e790558",
    "a2a inbox",
)

PEER_LIVENESS_PROBES = (
    "herdr pane get w4E:p6",
    "herdr pane list",
    "herdr pane process-info --pane w4E:p6",
    "herdr agent get w4E:p6",
    "herdr agent list",
    "a2a list",
    "kill -0 $peer_pid",
    "pgrep -f peer-agent",
    "ps -p $peer_pid",
)

PEER_POLL_LOOP_TEMPLATES = (
    "until {read} | grep -q DONE{exit}; do sleep 30; done",
    "while ! {read} | grep -q DONE{exit}; do sleep 30; done",
    "for i in $(seq 1 60); do {read} | grep -q DONE && break{exit}; sleep 30; done",
    "n=0\nuntil {read} | grep -q DONE{exit}\ndo\n  sleep 30\ndone",
)


def unlisted_rules(command, tool_name="Bash"):
    return sut.find_unlisted_background_wait_rules(command, tool_name)


class TestIncidentPeerReportPoll:
    def test_the_incident_poll_is_denied_for_lacking_a_liveness_exit(self):
        assert unlisted_rules(INCIDENT_PEER_REPORT_POLL) == [
            "peer-wait-without-liveness-exit"
        ]

    def test_the_incident_poll_is_denied_under_monitor_too(self):
        assert unlisted_rules(INCIDENT_PEER_REPORT_POLL, "Monitor") == [
            "peer-wait-without-liveness-exit"
        ]

    def test_the_same_poll_with_a_pane_liveness_exit_is_a_known_good_shape(self):
        assert unlisted_rules(INCIDENT_POLL_WITH_PANE_LIVENESS_EXIT) == []
        assert (
            sut.known_good_background_wait_shape(
                INCIDENT_POLL_WITH_PANE_LIVENESS_EXIT, "Bash"
            )
            == "peer-poll-with-liveness-exit"
        )


class TestEveryPeerPollNeedsALivenessProbeInsideItsLoop:
    @pytest.mark.parametrize(
        ("loop_template", "peer_state_read"),
        itertools.product(PEER_POLL_LOOP_TEMPLATES, PEER_STATE_READS),
    )
    def test_a_peer_poll_without_a_probe_is_denied(
        self, loop_template, peer_state_read
    ):
        command = loop_template.format(read=peer_state_read, exit="")
        assert unlisted_rules(command) == ["peer-wait-without-liveness-exit"]

    @pytest.mark.parametrize(
        ("loop_template", "peer_state_read", "liveness_probe"),
        itertools.product(
            PEER_POLL_LOOP_TEMPLATES, PEER_STATE_READS, PEER_LIVENESS_PROBES
        ),
    )
    def test_a_peer_poll_with_a_probe_in_the_loop_is_allowed(
        self, loop_template, peer_state_read, liveness_probe
    ):
        command = loop_template.format(
            read=peer_state_read, exit=f" || ! {liveness_probe} >/dev/null 2>&1"
        )
        assert unlisted_rules(command) == []
        assert (
            sut.known_good_background_wait_shape(command, "Bash")
            == "peer-poll-with-liveness-exit"
        )

    @pytest.mark.parametrize("liveness_probe", PEER_LIVENESS_PROBES)
    def test_a_probe_that_runs_only_after_the_loop_is_not_an_exit(self, liveness_probe):
        command = (
            "until herdr agent read w4E:p6 | grep -q DONE; do sleep 30; done; "
            f"{liveness_probe}"
        )
        assert unlisted_rules(command) == ["peer-wait-without-liveness-exit"]


class TestPeerEventStream:
    def test_orchestrator_watch_in_backgrounded_bash_is_denied(self):
        command = (
            "orchestrator watch --workspace w4E --pane w4E:p6 --timeout-minutes 10"
        )
        assert unlisted_rules(command, "Bash") == ["peer-event-stream-outside-monitor"]

    def test_orchestrator_watch_under_monitor_is_a_known_good_shape(self):
        command = (
            "orchestrator watch --workspace w4E --pane w4E:p6 --timeout-minutes 10"
        )
        assert unlisted_rules(command, "Monitor") == []
        assert (
            sut.known_good_background_wait_shape(command, "Monitor")
            == "peer-event-stream-under-monitor"
        )


class TestCommandsOutsideThePeerWaitRules:
    @pytest.mark.parametrize(
        "command",
        [
            "until ! pgrep -f darwin-rebuild; do sleep 15; done",
            "while ! curl -sf localhost:8767; do sleep 1; done",
            "until grep -q 'REBUILD-EXIT=' /tmp/rebuild.log; do sleep 5; done; tail -3 /tmp/rebuild.log",
            "for i in $(seq 1 45); do gh run list --commit abc123 --json conclusion | grep -q success && break; sleep 20; done",
        ],
    )
    def test_a_poll_of_a_process_file_ci_run_or_endpoint_is_a_condition_poll(
        self, command
    ):
        assert unlisted_rules(command) == []
        assert sut.known_good_background_wait_shape(command, "Bash") == "condition-poll"

    @pytest.mark.parametrize(
        "command",
        [
            "herdr agent wait w4E:p6 --until done --until blocked --timeout 3600000",
            "gh run watch 30957498339 --exit-status > /tmp/ci.log 2>&1",
            "pytest agent-harness/hooks/runtime/__tests__/unit/shell-commands/test_shell_heredoc_body.py",
            'for file in *.log; do gzip "$file"; done',
            'tail -f /var/log/app.log | while read -r line; do echo "$line"; done',
            "herdr agent read w4E:p6 --source visible | tail -20",
        ],
    )
    def test_a_native_wait_or_one_shot_job_is_not_a_background_wait(self, command):
        assert not sut.command_is_a_background_wait(command)
        assert unlisted_rules(command) == []

    def test_a_peer_read_after_a_file_poll_does_not_make_it_a_peer_poll(self):
        command = (
            "until [ -f /tmp/review.md ]; do sleep 10; done; "
            "herdr agent read w4E:p6 --source visible | tail -12"
        )
        assert unlisted_rules(command) == []

    def test_a_loop_keyword_inside_quoted_program_text_is_not_a_shell_loop(self):
        command = (
            "python3 -u -c \"\nwhile True:\n    poll('herdr agent read w4E:p6')\n\"; "
            "echo ready; do_nothing"
        )
        assert sut.shell_loop_span(command) is None
