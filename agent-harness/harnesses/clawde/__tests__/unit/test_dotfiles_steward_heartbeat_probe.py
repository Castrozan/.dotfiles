import io
import sys

import dotfiles_steward_heartbeat_probe as probe


def run_probe(
    monkeypatch, upstream: str, nightly_log_text: str | None, tmp_path
) -> str:
    log_file = tmp_path / "nightly-deep-test-tiers.log"
    if nightly_log_text is not None:
        log_file.write_text(nightly_log_text, encoding="utf-8")
    monkeypatch.setenv("DOTFILES_NIGHTLY_LOG_FILE", str(log_file))
    monkeypatch.setattr(probe, "upstream_fingerprint", lambda: upstream)
    output = io.StringIO()
    monkeypatch.setattr(sys, "stdout", output)
    assert probe.main() == 0
    return output.getvalue()


def test_silent_when_the_steward_has_nothing_and_no_night_ran(monkeypatch, tmp_path):
    assert run_probe(monkeypatch, "", None, tmp_path) == ""


def test_silent_when_the_last_night_passed(monkeypatch, tmp_path):
    passed = "=== --runtime exited 0 ===\nevery deep tier passed: --integration-scripts, --runtime\n"
    assert run_probe(monkeypatch, "", passed, tmp_path) == ""


def test_the_upstream_fingerprint_passes_through_untouched(monkeypatch, tmp_path):
    output = run_probe(monkeypatch, '{"verdict": "behind"}', None, tmp_path)
    assert output == '{"verdict": "behind"}\n'


def test_a_failed_night_wakes_the_steward_on_its_own(monkeypatch, tmp_path):
    failed = "=== --runtime exited 1 ===\nFAILED tiers: --runtime\n"
    output = run_probe(monkeypatch, "", failed, tmp_path)
    assert output.startswith(
        "nightly deep tiers: FAILED tiers: --runtime (log written "
    )


def test_a_night_that_could_not_run_wakes_the_steward(monkeypatch, tmp_path):
    could_not_run = "FAILED to run: dotfiles-test is not on PATH, so no tier can run\n"
    output = run_probe(monkeypatch, "", could_not_run, tmp_path)
    assert "FAILED to run: dotfiles-test is not on PATH" in output


def test_a_failed_night_and_steward_work_share_one_fingerprint(monkeypatch, tmp_path):
    output = run_probe(
        monkeypatch, '{"verdict": "behind"}', "FAILED tiers: --runtime\n", tmp_path
    )
    assert output.startswith(
        '{"verdict": "behind"} | nightly deep tiers: FAILED tiers: --runtime'
    )
