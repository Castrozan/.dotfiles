import json
import subprocess
from types import SimpleNamespace

import doctor
import pytest
from doctor import Finding


def answer(returncode=0, stdout=b"", stderr=b""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


class Machine:
    def __init__(self, answers):
        self.answers = answers
        self.commands = []

    def run(self, command, stdin=b""):
        self.commands.append(command)
        for fragment, reply in self.answers.items():
            if fragment in " ".join(command):
                if isinstance(reply, Exception):
                    raise reply
                return reply
        return answer()


HEALTHY_HOST = {
    "is-active": answer(stdout=b"active\n"),
    "avatar-transcribe": answer(),
}
HOST_REPORT = json.dumps(
    [{"name": "hex.service", "healthy": True, "detail": "active"}]
).encode()


def test_a_host_with_everything_running_is_healthy():
    findings = doctor.host_findings(Machine(HEALTHY_HOST).run)
    assert [finding.healthy for finding in findings] == [True, True, True]


def test_a_stopped_unit_is_named_with_its_state():
    machine = Machine({"hex.service": answer(3, b"inactive\n"), **HEALTHY_HOST})
    assert doctor.host_findings(machine.run)[0] == Finding(
        "hex.service", False, "inactive"
    )


def test_a_transcriber_that_refuses_reports_its_last_error_line():
    refusal = answer(1, stderr=b"Traceback\nConnectionError: Hex refused\n")
    machine = Machine({**HEALTHY_HOST, "avatar-transcribe": refusal})
    assert doctor.host_findings(machine.run)[-1] == Finding(
        "transcription", False, "ConnectionError: Hex refused"
    )


def seat(answers, serves=True):
    return doctor.seat_findings(Machine(answers).run, lambda address: serves, "hub")


def test_a_seat_relays_what_its_host_reports_under_the_host_name():
    findings = seat({"avatar-doctor": answer(stdout=HOST_REPORT)})
    assert Finding("hub: hex.service", True, "active") in findings
    assert all(finding.healthy for finding in findings)


def test_an_unreachable_host_is_the_finding_and_nothing_is_asked_of_it():
    machine = Machine({"hub true": answer(255, stderr=b"ssh: no route\n")})
    findings = doctor.seat_findings(machine.run, lambda address: True, "hub")
    assert findings[0] == Finding("reach hub", False, "ssh: no route")
    assert not any("avatar-doctor" in command for command in machine.commands)


def test_unloaded_mac_agents_are_reported():
    findings = seat(
        {"avatar-doctor": answer(stdout=HOST_REPORT), "launchctl": answer(113)}
    )
    assert Finding("wake agent", False, "not loaded") in findings
    assert Finding("conversation agent", False, "not loaded") in findings


@pytest.mark.parametrize(
    ("status", "healthy", "detail"),
    [
        (b'{"open": true}', True, "paused while a conversation listens"),
        (b'{"open": false}', False, "no capture page and no conversation"),
    ],
)
def test_a_silent_wake_page_is_healthy_only_while_a_conversation_listens(
    status, healthy, detail
):
    findings = seat(
        {
            "avatar-doctor": answer(stdout=HOST_REPORT),
            "avatar-talk": answer(stdout=status),
        },
        serves=False,
    )
    assert Finding("wake microphone", healthy, detail) in findings


def test_a_command_that_never_returns_becomes_a_finding_not_a_crash():
    stuck = subprocess.TimeoutExpired(["ssh"], doctor.COMMAND_SECONDS)
    machine = Machine({"hub true": stuck})
    findings = doctor.examined(
        lambda: doctor.seat_findings(machine.run, lambda address: True, "hub")
    )
    assert [finding.healthy for finding in findings] == [False]
    assert findings[0].name == "doctor"


def test_text_output_marks_each_finding_and_json_round_trips():
    findings = [Finding("a", True, "fine"), Finding("b", False, "broken")]
    assert doctor.rendered(findings, False) == "ok   a: fine\nFAIL b: broken"
    assert json.loads(doctor.rendered(findings, True))[1] == {
        "name": "b",
        "healthy": False,
        "detail": "broken",
    }


def test_a_seat_checks_its_own_transcription_even_when_the_host_is_gone():
    refusal = answer(1, stderr=b"ConnectionError: Hex refused\n")
    machine = Machine(
        {"hub true": answer(255, stderr=b"no route\n"), "avatar-transcribe": refusal}
    )
    findings = doctor.seat_findings(machine.run, lambda port: True, "hub")
    assert findings[-1] == Finding(
        "transcription", False, "ConnectionError: Hex refused"
    )
