import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from native_model_server import native_model_server
from native_opencode_profile import prepare_profile


def main():
    executable, runtime, agents = map(Path, sys.argv[1:])
    with tempfile.TemporaryDirectory(prefix="opencode-v2-evaluation-") as temporary:
        root = Path(temporary)
        with native_model_server() as model:
            environment, workspace = prepare_profile(
                root, agents, model_url=f"http://127.0.0.1:{model.server_port}/v1"
            )
            environment["PATH"] = (
                str(executable.parent) + os.pathsep + environment["PATH"]
            )
            fixture = workspace / "fixture.txt"
            fixture.write_text("NATIVE_READ_MARKER")
            try:
                for tool, tool_input, no_tools in [
                    ("read", {"path": str(fixture)}, False),
                    ("write", {"path": str(fixture), "content": "forbidden"}, False),
                    ("read", {"path": str(fixture)}, True),
                ]:
                    model.requests.clear()
                    result_file = root / "result.json"
                    result = subprocess.run(
                        ["node", str(runtime)],
                        input=json.dumps(
                            {
                                "harness": "opencode",
                                "model": "acceptance/fixture",
                                "working_directory": str(workspace),
                                "timeout": 10,
                                "system_prompt": "EVALUATION_SYSTEM_MARKER",
                                "no_tools": no_tools,
                                "prompt": json.dumps(
                                    {"tool": tool, "input": tool_input}
                                ),
                                "result_file": str(result_file),
                            }
                        ),
                        env=environment,
                        text=True,
                        capture_output=True,
                        timeout=15,
                    )
                    assert result.returncode == 0, result.stderr
                    outcome = json.loads(result_file.read_text())
                    assert outcome["error"] is None, outcome
                    assert outcome["output"] == "Acceptance complete.", outcome
                    assert fixture.read_text() == "NATIVE_READ_MARKER"
                    assert any(
                        "EVALUATION_SYSTEM_MARKER" in json.dumps(request)
                        for request in model.requests
                    )
                    tool_results = [
                        message
                        for request in model.requests
                        for message in request.get("messages", [])
                        if message.get("role") == "tool"
                    ]
                    assert tool_results, model.requests
                    if no_tools or tool == "write":
                        assert "No tool named" in json.dumps(tool_results), tool_results
                        assert all(
                            tool
                            not in [
                                entry["function"]["name"]
                                for entry in request.get("tools", [])
                            ]
                            for request in model.requests
                        )
                    else:
                        assert "NATIVE_READ_MARKER" in json.dumps(tool_results), (
                            tool_results
                        )
            finally:
                for directory in root.rglob("*"):
                    if directory.is_dir() and not directory.is_symlink():
                        directory.chmod(0o755)
    print(
        "Verified V2 evaluation SDK, read-only permissions, no-tools denial and system prompt"
    )


if __name__ == "__main__":
    main()
