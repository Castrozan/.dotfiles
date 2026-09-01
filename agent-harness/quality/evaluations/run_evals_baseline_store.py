import json
import tempfile
from pathlib import Path

BASELINE_PATH = Path(__file__).with_name("baseline.json")


def read_baseline(path: Path = BASELINE_PATH) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_baseline_checkpoint(
    baseline: dict, path: Path = BASELINE_PATH, announce: bool = False
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(baseline, temporary_file, indent=2)
            temporary_file.write("\n")
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    if announce:
        print(f"\nBaseline saved to {path}")
        print(f"  Pass rate: {baseline['pass_rate']:.1%}")
        print(f"  Tests: {baseline['total_passed']}/{baseline['total_tests']}")
        print(f"  Commit: {baseline['git_commit']}")
