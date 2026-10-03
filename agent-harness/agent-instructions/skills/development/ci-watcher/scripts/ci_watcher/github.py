import json
import subprocess


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
    passed = result["conclusion"] == "success"
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
