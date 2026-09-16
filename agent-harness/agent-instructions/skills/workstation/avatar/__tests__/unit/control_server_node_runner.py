import json
import shutil
import subprocess
from pathlib import Path

import pytest

CONTROL_SERVER_DIRECTORY = (
    Path(__file__).resolve().parents[2] / "scripts" / "control-server"
)

ISOLATED_DEPENDENCY_PACKAGES = ("ws", "express")

requires_node = pytest.mark.skipif(
    shutil.which("node") is None,
    reason="node is not available on this machine",
)


def domain_javascript_files():
    return [
        path
        for path in sorted(CONTROL_SERVER_DIRECTORY.rglob("*.js"))
        if "node_modules" not in path.parts and "dependencies" not in path.parts
    ]


def adapter_javascript_files():
    return sorted((CONTROL_SERVER_DIRECTORY / "dependencies").rglob("*.js"))


def run_node_expression(javascript_source):
    completed = subprocess.run(
        ["node", "--input-type=commonjs", "-e", javascript_source],
        cwd=CONTROL_SERVER_DIRECTORY,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"node exited {completed.returncode}\nstdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return completed.stdout


RESULT_MARKER = "__CONTROL_SERVER_RESULT__"


def evaluate_node_json(javascript_source):
    wrapped = (
        f"{javascript_source}\n"
        f"Promise.resolve(result).then((resolvedResult) => "
        f'console.log("{RESULT_MARKER}" + JSON.stringify(resolvedResult)));\n'
    )
    output = run_node_expression(wrapped)
    payloads = [
        line[len(RESULT_MARKER) :]
        for line in output.splitlines()
        if line.startswith(RESULT_MARKER)
    ]
    if len(payloads) != 1:
        raise AssertionError(
            f"expected exactly one result marker, got {len(payloads)}\n{output}"
        )
    return json.loads(payloads[0])
