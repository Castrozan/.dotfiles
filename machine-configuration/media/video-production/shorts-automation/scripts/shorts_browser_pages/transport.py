import json
import os
import subprocess
from pathlib import Path


def browser_environment(scope):
    return dict(
        os.environ, OPENCLI_JOB_SCOPE=scope, OPENCLI_BRIDGE_TOKEN=job_token(scope)
    )


def job_token(scope):
    return json.loads((Path(scope) / "OpenCLIBridge/job-token.json").read_text())[
        "token"
    ]


def browser_result(command, arguments, scope):
    result = subprocess.run(
        [*command, *arguments],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
        env=browser_environment(scope),
    )
    return json.loads(result.stdout)["data"]


def create_page(command, scope):
    return browser_result(command, ["tab", "new"], scope)["page"]


def list_pages(command, sessions, scope):
    targets = {}
    for session in set(sessions.values()):
        for target in browser_result([*command[:3], session], ["tab", "list"], scope):
            targets[target["page"]] = dict(target, id=target["page"])
    return list(targets.values())
