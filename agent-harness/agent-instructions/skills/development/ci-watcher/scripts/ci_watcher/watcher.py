import argparse
import json
from pathlib import Path
import signal
import subprocess
import tempfile

from forge.repository import resolve_repository
from ci_watcher.github import wait_for_run, retain_result
from ci_watcher.gitlab import watch_gitlab


def positive_integer(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def arguments():
    parser = argparse.ArgumentParser(
        prog="ci-watcher",
        description="Wait quietly for one hosted CI run, then retain its verdict and logs.",
        epilog="Exit codes: 0 passed, 1 failed, 2 watcher error, 124 timeout, 130 interrupted. Remote CI is never cancelled.",
    )
    parser.add_argument(
        "run", type=positive_integer, help="GitHub run or GitLab pipeline ID"
    )
    parser.add_argument(
        "--repo",
        help="full Git URL or project path; defaults to the current Git upstream",
    )
    parser.add_argument(
        "--provider",
        choices=["github", "gitlab"],
        help="provider for an unregistered enterprise host",
    )
    parser.add_argument(
        "--timeout",
        type=positive_integer,
        default=3600,
        help="maximum wait in seconds (default: 3600)",
    )
    return parser.parse_args()


def watch(run, repository=None, timeout=3600, provider=None):
    directory = Path(tempfile.mkdtemp(prefix=f"ci-watcher-{run}-"))
    print(f"Watching run {run}; report directory: {directory}", flush=True)
    try:
        context = resolve_repository(repository=repository, provider=provider)
        if context.provider == "gitlab":
            result, status = watch_gitlab(context, run, directory, timeout)
        else:
            target = [str(run), "--repo", context.url]
            watcher_status = wait_for_run(target, directory, timeout)
            result, status = retain_result(target, directory, watcher_status)
        result.update({"provider": context.provider, "repository": context.url})
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
    return watch(options.run, options.repo, options.timeout, options.provider)
