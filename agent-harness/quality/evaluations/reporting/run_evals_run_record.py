import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

RUN_RECORD_ROOT = (
    Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser()
    / "agent-eval"
    / "runs"
)


@dataclass(frozen=True)
class EvaluationRunRecord:
    results_path: Path

    def record(self, result, epoch: int = 1) -> None:
        row = {
            "category": result.category,
            "name": result.name,
            "epoch": epoch,
            "passed": result.passed,
            "duration": result.duration,
            "assertions_failed": result.assertions_failed,
            "error": result.error,
            "output": result.output,
        }
        with self.results_path.open("a", encoding="utf-8") as results_file:
            results_file.write(json.dumps(row, ensure_ascii=False) + "\n")


class DiscardedRunRecord:
    results_path = None

    def record(self, result, epoch: int = 1) -> None:
        pass


def open_run_record(root: Path = RUN_RECORD_ROOT) -> EvaluationRunRecord:
    root.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_directory = Path(tempfile.mkdtemp(prefix=f"{started_at}-", dir=root))
    return EvaluationRunRecord(run_directory / "results.jsonl")
