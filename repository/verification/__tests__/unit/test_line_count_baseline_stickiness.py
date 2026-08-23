import json
import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CHECKER_RELATIVE_PATH = "repository/verification/check-line-counts.py"
BASELINE_RELATIVE_PATH = "repository/verification/line-count-baseline.json"
POLICY_RELATIVE_PATH = "agent-harness/hooks/runtime/post-tool-use/line-count"
POLICY_MODULE_NAMES = ("line_count_policy.py", "line_count_baseline.py")


def write_file_with_line_count(file_path: Path, line_count: int) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("\n".join(f"line_{n}" for n in range(line_count)) + "\n")


def make_checkout(
    root: Path, tracked_line_counts: dict[str, int], recorded_ceilings: dict[str, int]
) -> Path:
    checker_path = root / CHECKER_RELATIVE_PATH
    checker_path.parent.mkdir(parents=True)
    shutil.copy(REPOSITORY_ROOT / CHECKER_RELATIVE_PATH, checker_path)
    policy_directory = root / POLICY_RELATIVE_PATH
    policy_directory.mkdir(parents=True)
    for module_name in POLICY_MODULE_NAMES:
        shutil.copy(
            REPOSITORY_ROOT / POLICY_RELATIVE_PATH / module_name,
            policy_directory / module_name,
        )
    (root / BASELINE_RELATIVE_PATH).write_text(
        json.dumps(recorded_ceilings, indent=2) + "\n"
    )
    for relative_path, line_count in tracked_line_counts.items():
        write_file_with_line_count(root / relative_path, line_count)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(
        ["git", "-C", str(root), "add", "--", *tracked_line_counts], check=True
    )
    return root


def run_checker(root: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(root / CHECKER_RELATIVE_PATH), *arguments],
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_passes_when_every_recorded_ceiling_still_matches(tmp_path):
    checkout = make_checkout(tmp_path, {"legacy.py": 300}, {"legacy.py": 300})
    result = run_checker(checkout)
    assert result.returncode == 0, result.stderr


def test_fails_when_a_grandfathered_file_grows(tmp_path):
    checkout = make_checkout(tmp_path, {"legacy.py": 301}, {"legacy.py": 300})
    result = run_checker(checkout)
    assert result.returncode == 1
    assert "grew from 300 to 301" in result.stderr


def test_fails_when_a_recorded_file_no_longer_exists(tmp_path):
    checkout = make_checkout(
        tmp_path, {"legacy.py": 300}, {"legacy.py": 300, "gone.py": 400}
    )
    result = run_checker(checkout)
    assert result.returncode == 1
    assert "gone.py" in result.stderr


def test_fails_when_a_recorded_file_dropped_back_under_the_limit(tmp_path):
    checkout = make_checkout(tmp_path, {"legacy.py": 150}, {"legacy.py": 300})
    result = run_checker(checkout)
    assert result.returncode == 1
    assert "no longer a tracked file over the limit" in result.stderr


def test_fails_when_a_grandfathered_file_shrank_but_stays_over_the_limit(tmp_path):
    checkout = make_checkout(tmp_path, {"legacy.py": 250}, {"legacy.py": 300})
    result = run_checker(checkout)
    assert result.returncode == 1
    assert "shrank from 300 to 250" in result.stderr, (
        "a file that gives up lines must give up the ceiling with them, or the "
        "baseline keeps reserving room the file no longer uses"
    )


def test_fails_when_an_unrecorded_file_exceeds_the_limit(tmp_path):
    checkout = make_checkout(tmp_path, {"fresh.py": 201}, {"legacy.py": 300})
    result = run_checker(checkout)
    assert result.returncode == 1
    assert "new offender at 201 lines" in result.stderr


def test_update_baseline_drops_stale_entries_and_records_the_lower_count(tmp_path):
    checkout = make_checkout(
        tmp_path, {"legacy.py": 250}, {"legacy.py": 300, "gone.py": 400}
    )
    assert run_checker(checkout, "--update-baseline").returncode == 0
    assert json.loads((checkout / BASELINE_RELATIVE_PATH).read_text()) == {
        "legacy.py": 250
    }
    assert run_checker(checkout).returncode == 0
