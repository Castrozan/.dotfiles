import argparse
import json
from pathlib import Path
import signal
import subprocess
import tempfile


def positive_integer(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def arguments():
    parser = argparse.ArgumentParser(
        prog="ci-watcher",
        description="Wait quietly for one GitHub Actions run, then retain its verdict and logs.",
        epilog="Exit codes: 0 passed, 1 failed, 2 watcher error, 124 timeout, 130 interrupted. Remote CI is never cancelled.",
    )
    parser.add_argument("run", type=positive_integer, help="GitHub Actions run ID")
    parser.add_argument(
        "--repo",
        help="GitHub repository OWNER/REPO; defaults to the current repository",
    )
    parser.add_argument(
        "--timeout",
        type=positive_integer,
        default=3600,
        help="maximum wait in seconds (default: 3600)",
    )
    return parser.parse_args()


def stop_process(process):
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def wait_for_run(target, directory, timeout):
    with (directory / "watch.log").open("w") as output:
        process = subprocess.Popen(
            [
                "gh",
                "run",
                "watch",
                *target,
                "--compact",
                "--exit-status",
                "--interval",
                "30",
            ],
            stdout=output,
            stderr=subprocess.STDOUT,
        )
        try:
            return process.wait(timeout=timeout)
        except (KeyboardInterrupt, subprocess.TimeoutExpired):
            stop_process(process)
            raise


def retain_result(target, directory, watcher_status):
    response = subprocess.run(
        [
            "gh",
            "run",
            "view",
            *target,
            "--json",
            "databaseId,attempt,headSha,status,conclusion,url,jobs",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    result = json.loads(response.stdout)
    if result["status"] != "completed":
        raise RuntimeError(f"Watcher exited {watcher_status} before the run completed")
    passed = result["conclusion"] in {"success", "neutral", "skipped"}
    if passed and watcher_status != 0:
        raise RuntimeError(f"Watcher exited {watcher_status}; inspect watch.log")
    with (directory / "run.log").open("w") as output:
        subprocess.run(
            [
                "gh",
                "run",
                "view",
                *target,
                "--attempt",
                str(result["attempt"]),
                "--log",
            ],
            stdout=output,
            stderr=subprocess.STDOUT,
            timeout=120,
            check=True,
        )
    return {**result, "outcome": "passed" if passed else "failed"}, 0 if passed else 1


def watch(run, repository=None, timeout=3600):
    directory = Path(tempfile.mkdtemp(prefix=f"ci-watcher-{run}-"))
    target = [str(run)]
    if repository:
        target.extend(["--repo", repository])
    print(f"Watching run {run}; report directory: {directory}", flush=True)
    try:
        watcher_status = wait_for_run(target, directory, timeout)
        result, status = retain_result(target, directory, watcher_status)
    except KeyboardInterrupt:
        result, status = {"outcome": "interrupted"}, 130
    except subprocess.TimeoutExpired:
        result, status = {"outcome": "timeout"}, 124
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        subprocess.CalledProcessError,
    ) as error:
        result, status = {"outcome": "error", "error": str(error)}, 2
    result.update({"run": run, "report_directory": str(directory), "exit_code": status})
    (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: result[key]
                for key in ("outcome", "url", "report_directory", "exit_code", "error")
                if key in result
            }
        ),
        flush=True,
    )
    return status


def interrupt(signum, frame):
    raise KeyboardInterrupt


def main():
    options = arguments()
    signal.signal(signal.SIGTERM, interrupt)
    return watch(options.run, options.repo, options.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
