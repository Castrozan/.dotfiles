import background_wait_shape_classifier as sut
import pytest
import wait_target_event_replacements as replacements

INCIDENT_PEER_REPORT_POLL = (
    "first=$(orchestrator heartbeat show Reviewer-w4E-p6 2>/dev/null | head -1); n=0; "
    'until { cur=$(orchestrator heartbeat show Reviewer-w4E-p6 2>/dev/null | head -1); [ "$cur" != "$first" ] '
    '&& echo "$cur" | grep -qE "· (done|blocked) · "; } || [ $n -ge 240 ]; '
    "do sleep 45; n=$((n+1)); done; orchestrator heartbeat show Reviewer-w4E-p6"
)

CAPPED_MERGE_REQUEST_POLL = (
    "for i in $(seq 1 120); do "
    "state=$(glab api 'projects/group%2Fplugin/merge_requests/118' | jq -r .state); "
    '[ "$state" != opened ] && break; sleep 30; done; echo "merge request: $state"'
)
UNCAPPED_MERGE_REQUEST_POLL = (
    "until [ \"$(glab api 'projects/group%2Fplugin/merge_requests/118' "
    '| jq -r .state)" = merged ]; do sleep 30; done'
)


def denied(command, tool_name="Bash", runs_in_background=False):
    return sut.find_denied_delay_wait(command, tool_name, runs_in_background)


class TestPeerPolls:
    @pytest.mark.parametrize(
        ("tool_name", "runs_in_background"),
        [("Bash", False), ("Bash", True), ("Monitor", False)],
    )
    def test_the_incident_poll_is_denied_in_every_context(
        self, tool_name, runs_in_background
    ):
        assert denied(INCIDENT_PEER_REPORT_POLL, tool_name, runs_in_background) == (
            sut.DelayWait("sleep-paced-loop", "peer-agent")
        )

    def test_a_liveness_probe_no_longer_buys_a_peer_poll_its_place(self):
        command = INCIDENT_PEER_REPORT_POLL.replace(
            "|| [ $n -ge 240 ]", "|| ! herdr pane get w4E:p6 >/dev/null 2>&1"
        )
        assert denied(command, "Bash", True).target_name == "peer-agent"


class TestRemoteStateSafetyNet:
    @pytest.mark.parametrize(
        ("tool_name", "runs_in_background"), [("Bash", True), ("Monitor", False)]
    )
    def test_a_capped_remote_poll_off_the_session_is_a_known_good_shape(
        self, tool_name, runs_in_background
    ):
        assert denied(CAPPED_MERGE_REQUEST_POLL, tool_name, runs_in_background) is None
        assert (
            sut.known_good_background_wait_shape(CAPPED_MERGE_REQUEST_POLL, tool_name)
            == "remote-state-safety-net"
        )

    def test_the_same_poll_in_the_foreground_is_denied(self):
        assert denied(CAPPED_MERGE_REQUEST_POLL) == sut.DelayWait(
            "sleep-paced-loop", "forge-merge-request"
        )

    def test_an_uncapped_remote_poll_in_background_bash_needs_a_cap(self):
        executed_text = UNCAPPED_MERGE_REQUEST_POLL
        assert sut.find_unlisted_background_wait_rules(executed_text, "Bash") == [
            "forge-poll-without-cap"
        ]
        assert sut.known_good_background_wait_shape(executed_text, "Bash") is None

    def test_a_remote_poll_that_also_reads_a_local_file_has_an_event(self):
        command = (
            "until grep -q CHAIN-DONE /tmp/chain.log; do sleep 30; done; "
            + UNCAPPED_MERGE_REQUEST_POLL
        )
        assert denied(command, "Bash", True).target_name == "file-content"


class TestPeerEventStream:
    def test_orchestrator_watch_in_backgrounded_bash_is_denied(self):
        command = "orchestrator watch --workspace w4E --pane w4E:p6"
        assert sut.find_unlisted_background_wait_rules(command, "Bash") == [
            "peer-event-stream-outside-monitor"
        ]

    def test_orchestrator_watch_under_monitor_is_a_known_good_shape(self):
        command = "orchestrator watch --workspace w4E --pane w4E:p6"
        assert sut.find_unlisted_background_wait_rules(command, "Monitor") == []
        assert (
            sut.known_good_background_wait_shape(command, "Monitor")
            == "peer-event-stream-under-monitor"
        )


class TestNativeWaitsAreNotDelays:
    @pytest.mark.parametrize(
        "command",
        [
            "herdr agent wait w4E:p6 --until done --until blocked --timeout 3600000",
            "gh run watch 30957498339 --interval 10 --exit-status > /tmp/ci.log 2>&1",
            "wait-for-event file /tmp/rebuild.log --match 'REBUILD_EXIT='",
            'for file in *.log; do gzip "$file"; done',
            'tail -f /var/log/app.log | while read -r line; do echo "$line"; done',
        ],
    )
    def test_a_native_wait_or_one_shot_job_is_not_a_background_wait(self, command):
        assert not sut.command_is_a_background_wait(command)
        assert denied(command, "Bash", True) is None


class TestDenyReason:
    @pytest.mark.parametrize(
        "target_name", sorted(replacements.EVENT_REPLACEMENT_BY_WAIT_TARGET)
    )
    def test_every_denial_fits_two_lines_and_ends_on_the_event_to_wait_on(
        self, target_name
    ):
        reason = sut.build_delay_wait_deny_reason(
            sut.DelayWait("sleep-paced-loop", target_name), "This Bash command"
        )
        first_line, event_line = reason.split("\n")
        assert target_name in first_line
        assert event_line.endswith(
            replacements.EVENT_REPLACEMENT_BY_WAIT_TARGET[target_name]
        )
        assert len(reason) <= 400
