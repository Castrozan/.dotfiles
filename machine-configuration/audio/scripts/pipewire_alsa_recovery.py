import json
import re
import subprocess
import time
from collections import deque
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AlsaFailure:
    process_id: str
    device: str
    timestamp: float


def journal_string(entry, name):
    value = entry.get(name)
    return value if isinstance(value, str) else ""


def parse_failure(line):
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(entry, dict):
        return None
    match = re.search(
        r"spa\.alsa: (\S+): \(\d+ suppressed\) "
        r"snd_pcm_avail after recover: Broken pipe$",
        journal_string(entry, "MESSAGE"),
    )
    process_id = journal_string(entry, "_PID")
    timestamp = journal_string(entry, "__MONOTONIC_TIMESTAMP")
    if not all((match, process_id.isdecimal(), timestamp.isdecimal())):
        return None
    return AlsaFailure(process_id, match[1], int(timestamp) / 1_000_000)


@dataclass
class RecoveryPolicy:
    failures: deque = field(default_factory=lambda: deque(maxlen=32))
    next_recovery_time: float = 0

    def matching_timestamps(self, failure, earliest):
        return [
            recorded.timestamp
            for recorded in self.failures
            if recorded.process_id == failure.process_id
            and recorded.device == failure.device
            and recorded.timestamp >= earliest
        ]

    def should_recover(self, failure, now):
        if not all(
            (
                now >= self.next_recovery_time,
                now - 10 <= failure.timestamp <= now,
                failure not in self.failures,
            )
        ):
            return False
        self.failures.append(failure)
        matching = self.matching_timestamps(failure, now - 10)
        if len(matching) < 3 or max(matching) - min(matching) < 4:
            return False
        self.failures.clear()
        self.next_recovery_time = now + 60
        return True


def recover_audio(failure):
    current_process = subprocess.run(
        [
            "systemctl",
            "--user",
            "show",
            "--property=MainPID",
            "--value",
            "pipewire.service",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    ).stdout.strip()
    if current_process != failure.process_id:
        return
    print(f"Persistent ALSA recovery failure on {failure.device}; restarting audio")
    subprocess.run(
        [
            "systemctl",
            "--user",
            "restart",
            "pipewire.service",
            "pipewire-pulse.service",
            "wireplumber.service",
        ],
        check=True,
        timeout=20,
    )


def monitor_failures(entries):
    policy = RecoveryPolicy()
    for line in entries:
        failure = parse_failure(line)
        if failure is None or not policy.should_recover(failure, time.monotonic()):
            continue
        try:
            recover_audio(failure)
        except (subprocess.SubprocessError, OSError) as error:
            print(f"Audio recovery failed: {error}")


def main():
    journal = subprocess.Popen(
        [
            "journalctl",
            "--user",
            "--unit=pipewire.service",
            "--boot",
            "--follow",
            "--lines=0",
            "--output=json",
            "--output-fields=MESSAGE,_PID,__MONOTONIC_TIMESTAMP",
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        monitor_failures(journal.stdout)
        raise SystemExit(journal.wait() or 1)
    finally:
        journal.terminate()
        try:
            journal.wait(timeout=5)
        except subprocess.TimeoutExpired:
            journal.kill()
            journal.wait()


if __name__ == "__main__":
    main()
