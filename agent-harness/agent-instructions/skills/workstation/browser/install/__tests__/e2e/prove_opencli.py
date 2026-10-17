import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone
from http.server import HTTPServer
from pathlib import Path

from opencli_fixture import Fixture, clean
from opencli_restrictions import verify_restrictions


def main():
    parser = argparse.ArgumentParser(
        description="Exercise OpenCLI reads, UI, isolation and cleanup without posting or publishing."
    )
    parser.add_argument(
        "--opencli",
        default=shutil.which("opencli"),
        required=shutil.which("opencli") is None,
    )
    parser.add_argument(
        "--runner",
        default=shutil.which("opencli-run"),
        required=shutil.which("opencli-run") is None,
    )
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    options.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    assert clean(), "An existing OpenCLI job prevents an exclusive acceptance trial"
    with tempfile.TemporaryDirectory(prefix="opencli-proof-") as temporary:
        environment = dict(
            os.environ,
            XDG_DATA_HOME=f"{temporary}/data",
            XDG_STATE_HOME=f"{temporary}/state",
        )
        checks = verify_workflows(options, environment)
        checks.update(
            verify_restrictions(
                options.runner, options.output, "acceptance", environment
            )
        )
        public = subprocess.run(
            [options.opencli, "hackernews", "top", "--limit", "3"],
            capture_output=True,
            text=True,
            timeout=45,
            env=environment,
        )
        checks["public_adapter_returns_three_structured_records"] = (
            public.returncode == 0 and len(json.loads(public.stdout)["data"]) == 3
        )
        checks["zero_owned_processes_after_public_adapter"] = clean()
        article = subprocess.run(
            [
                options.opencli,
                "web",
                "read",
                "--url",
                "https://github.com/jackwener/OpenCLI",
                "--stdout",
                "true",
                "--download-images",
                "false",
                "--wait",
                "1",
            ],
            capture_output=True,
            text=True,
            timeout=90,
            env=environment,
        )
        checks["browser_adapter_automatically_starts_owned_job"] = (
            article.returncode == 0
            and "OpenCLI" in article.stdout
            and len(article.stdout) > 500
        )
        checks["zero_owned_processes_after_automatic_browser_adapter"] = clean()
    report = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "platform": sys.platform,
        "opencli_version": "2.0.0",
        "checks": checks,
        "passed": sum(checks.values()),
        "total": len(checks),
        "posting_or_publishing_exercised": False,
    }
    (options.output / "proof.json").write_text(json.dumps(report, indent=2) + chr(10))
    print(json.dumps(report, indent=2))
    assert all(checks.values()), checks


def verify_workflows(options, environment):
    server = HTTPServer(("127.0.0.1", 0), Fixture)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        workflow = Path(__file__).with_name("opencli_workflow.py")
        command = [
            options.runner,
            "--profile",
            "acceptance",
            "--timeout",
            "180",
            "--",
            sys.executable,
            str(workflow),
            f"http://127.0.0.1:{server.server_port}",
            str(options.output.resolve()),
        ]
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=230, env=environment
        )
        (options.output / "workflow.log").write_text(result.stdout + result.stderr)
        assert result.returncode == 0, result.stdout + result.stderr
        checks = json.loads(result.stdout.strip().splitlines()[-1])
        checks["zero_owned_processes_after_success"] = clean()
        persistence = subprocess.run(
            [*command, "--persist"],
            capture_output=True,
            text=True,
            timeout=70,
            env=environment,
        )
        assert persistence.returncode == 0, persistence.stdout + persistence.stderr
        checks.update(json.loads(persistence.stdout.strip().splitlines()[-1]))
        checks["zero_owned_processes_after_persistence"] = clean()
        return checks
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
