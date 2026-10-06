from dataclasses import dataclass
import subprocess

TIMED_OUT_EXIT_CODE = 124


@dataclass(frozen=True)
class ProbeOutcome:
    category: str
    name: str
    status: str
    reason: str


def run_bash_snippet(
    snippet: str, probe_timeout_seconds: str, capture_stdout: bool
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["timeout", probe_timeout_seconds, "bash", "-c", snippet],
        stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def evaluate_probe(probe: dict, probe_timeout_seconds: str) -> ProbeOutcome:
    applicability = probe["applicableWhen"] or ""
    applicability_outcome = _evaluate_probe_applicability(
        probe, applicability, probe_timeout_seconds
    )
    if applicability_outcome is not None:
        return applicability_outcome
    return _evaluate_probe_body(probe, probe_timeout_seconds)


def _evaluate_probe_applicability(
    probe: dict, applicability: str, probe_timeout_seconds: str
) -> ProbeOutcome | None:
    if not applicability:
        return None
    applicability_run = run_bash_snippet(
        applicability, probe_timeout_seconds, capture_stdout=True
    )
    applicability_reason = applicability_run.stdout.decode(errors="replace").rstrip(
        "\n"
    )
    if applicability_run.returncode == TIMED_OUT_EXIT_CODE:
        return _probe_outcome(
            probe,
            "fail",
            f"applicability check timed out after {probe_timeout_seconds}s",
        )
    if applicability_run.returncode != 0:
        return _probe_outcome(probe, "skip", applicability_reason or "not applicable")
    return None


def _evaluate_probe_body(probe: dict, probe_timeout_seconds: str) -> ProbeOutcome:
    body_run = run_bash_snippet(
        probe["probe"], probe_timeout_seconds, capture_stdout=False
    )
    if body_run.returncode == 0:
        return _probe_outcome(probe, "pass", "")
    if body_run.returncode == TIMED_OUT_EXIT_CODE:
        return _probe_outcome(
            probe, "fail", f"timed out after {probe_timeout_seconds}s"
        )
    return _probe_outcome(probe, "fail", "")


def _probe_outcome(probe: dict, status: str, reason: str) -> ProbeOutcome:
    return ProbeOutcome(probe["category"], probe["name"], status, reason)
