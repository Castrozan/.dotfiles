import sys
import time


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes, remainder = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m{remainder:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes:02d}m"


class EvaluationProgressReporter:
    def __init__(self, total_tests: int, max_workers: int, stream=None):
        self.total_tests = total_tests
        self.max_workers = max_workers
        self.stream = stream if stream is not None else sys.stdout
        self.started_at = time.monotonic()
        self.completed = 0
        self.passed = 0
        self.slowest_test = ("", 0.0)

    def elapsed_seconds(self) -> float:
        return time.monotonic() - self.started_at

    def estimated_remaining_seconds(self) -> float | None:
        if self.completed == 0:
            return None
        per_test = self.elapsed_seconds() / self.completed
        return per_test * (self.total_tests - self.completed)

    def announce_start(self) -> None:
        self.write(
            f"Running {self.total_tests} evals across {self.max_workers} workers; "
            f"one line per finished test\n"
        )

    def record(self, result) -> None:
        self.completed += 1
        if result.passed:
            self.passed += 1
        if result.duration > self.slowest_test[1]:
            self.slowest_test = (result.name, result.duration)
        self.write(self.progress_line(result))

    def progress_line(self, result) -> str:
        width = len(str(self.total_tests))
        remaining = self.estimated_remaining_seconds()
        eta = (
            "eta unknown" if remaining is None else f"eta {format_duration(remaining)}"
        )
        return (
            f"[{self.completed:>{width}}/{self.total_tests}] "
            f"{'ok  ' if result.passed else 'FAIL'} "
            f"{result.category}/{result.name} {result.duration:.1f}s | "
            f"pass-rate {self.passed / self.completed:.1%} "
            f"({self.passed}/{self.completed}) | "
            f"elapsed {format_duration(self.elapsed_seconds())} | {eta}\n"
        )

    def announce_finish(self) -> None:
        failed = self.completed - self.passed
        slowest_name, slowest_duration = self.slowest_test
        self.write(
            f"Finished {self.completed} evals in "
            f"{format_duration(self.elapsed_seconds())}: {self.passed} passed, "
            f"{failed} failed; slowest {slowest_name} "
            f"{format_duration(slowest_duration)}\n"
        )

    def write(self, text: str) -> None:
        self.stream.write(text)
        self.stream.flush()
