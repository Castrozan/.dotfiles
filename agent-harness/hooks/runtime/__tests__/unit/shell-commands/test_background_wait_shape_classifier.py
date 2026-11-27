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


def denied(command):
    return sut.delay_wait_in(command)


class TestPeerPolls:
    def test_the_incident_poll_is_a_delay_wait_on_its_peer(self):
        assert denied(INCIDENT_PEER_REPORT_POLL) == (
            sut.DelayWait("sleep-paced-loop", "peer-agent")
        )

    def test_a_liveness_probe_no_longer_buys_a_peer_poll_its_place(self):
        command = INCIDENT_PEER_REPORT_POLL.replace(
            "|| [ $n -ge 240 ]", "|| ! herdr pane get w4E:p6 >/dev/null 2>&1"
        )
        assert denied(command).target_name == "peer-agent"


class TestRemotePolls:
    def test_a_capped_remote_poll_is_a_delay_wait_on_the_merge_request(self):
        assert denied(CAPPED_MERGE_REQUEST_POLL) == sut.DelayWait(
            "sleep-paced-loop", "forge-merge-request"
        )

    def test_no_remote_poll_is_a_known_good_shape(self):
        for tool_name in ("Bash", "Monitor"):
            assert (
                sut.known_good_background_wait_shape(
                    CAPPED_MERGE_REQUEST_POLL, tool_name
                )
                is None
            )
            assert (
                sut.find_unlisted_background_wait_rules(
                    CAPPED_MERGE_REQUEST_POLL, tool_name
                )
                == []
            )


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
        assert denied(command) is None


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
