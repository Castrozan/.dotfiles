import argparse
import dataclasses
import http.client
import json
import os
import subprocess
import sys

COMMAND_SECONDS = 15
SILENCE = bytes(16000)
HOST_UNITS = ["hex.service", "avatar-wake.service"]
WAKE_AGENT = "com.dotfiles.avatar-wake"
WAKE_PAGE_PORT = 8771
REACH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5"]
UNREACHABLE = (OSError, subprocess.SubprocessError, ValueError)


@dataclasses.dataclass(frozen=True)
class Finding:
    name: str
    healthy: bool
    detail: str


def run_command(command, stdin=b""):
    return subprocess.run(
        command, input=stdin, capture_output=True, timeout=COMMAND_SECONDS
    )


def page_serves(port):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        connection.request("GET", "/")
        return connection.getresponse().status == 200
    except (OSError, http.client.HTTPException):
        return False
    finally:
        connection.close()


def last_line(output):
    lines = output.decode(errors="replace").strip().splitlines()
    return lines[-1] if lines else ""


def unit_active(run, unit):
    state = last_line(run(["systemctl", "--user", "is-active", unit]).stdout)
    return Finding(unit, state == "active", state or "unknown")


def transcriber_answers(run):
    answered = run(["avatar-transcribe"], SILENCE)
    healthy = answered.returncode == 0
    return Finding(
        "transcription", healthy, "answers" if healthy else last_line(answered.stderr)
    )


def host_findings(run):
    return [*(unit_active(run, unit) for unit in HOST_UNITS), transcriber_answers(run)]


def host_reachable(run, host):
    reached = run([*REACH, host, "true"])
    healthy = reached.returncode == 0
    return Finding(
        f"reach {host}", healthy, "reachable" if healthy else last_line(reached.stderr)
    )


def findings_reported_by(run, host):
    reported = json.loads(run([*REACH, host, "avatar-doctor", "--json"]).stdout)
    return [
        Finding(f"{host}: {entry['name']}", entry["healthy"], entry["detail"])
        for entry in reported
    ]


def wake_agent_loaded(run):
    target = f"gui/{os.getuid()}/{WAKE_AGENT}"
    loaded = run(["launchctl", "print", target]).returncode == 0
    return Finding("wake agent", loaded, "loaded" if loaded else "not loaded")


def conversation_open(run):
    return json.loads(run(["avatar-talk", "status"]).stdout).get("open", False)


def wake_microphone_hears(run, serves):
    if serves(WAKE_PAGE_PORT):
        return Finding("wake microphone", True, "capturing")
    if conversation_open(run):
        return Finding("wake microphone", True, "paused while a conversation listens")
    return Finding("wake microphone", False, "no capture page and no conversation")


def seat_findings(run, serves, host):
    reach = host_reachable(run, host)
    if not reach.healthy:
        return [reach, wake_agent_loaded(run)]
    return [
        reach,
        *findings_reported_by(run, host),
        wake_agent_loaded(run),
        wake_microphone_hears(run, serves),
    ]


def examined(examine):
    try:
        return examine()
    except UNREACHABLE as error:
        return [Finding("doctor", False, f"{type(error).__name__}: {error}")]


def rendered(findings, as_json):
    if as_json:
        return json.dumps([dataclasses.asdict(finding) for finding in findings])
    return "\n".join(
        f"{'ok  ' if finding.healthy else 'FAIL'} {finding.name}: {finding.detail}"
        for finding in findings
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--seat-of")
    arguments = parser.parse_args()
    if arguments.seat_of:
        findings = examined(
            lambda: seat_findings(run_command, page_serves, arguments.seat_of)
        )
    else:
        findings = examined(lambda: host_findings(run_command))
    print(rendered(findings, arguments.json))
    sys.exit(0 if all(finding.healthy for finding in findings) else 1)


if __name__ == "__main__":
    main()
