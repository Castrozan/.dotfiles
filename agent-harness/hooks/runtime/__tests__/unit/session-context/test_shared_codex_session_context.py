import json
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from flat_deploy_test_support import (
    flatten_into_single_runtime_directory,
    run_flattened_hook,
)
from herdr_socket_double import RecordingHerdrSocketServer

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[5] / "harnesses/codex/scripts/shared_server"),
)


@pytest.mark.parametrize("source", ["startup", "resume", "compact"])
def test_shared_session_hooks_deliver_current_instructions_and_report_only_the_owned_pane(
    tmp_path, source
):
    from codex_client_context import ClientContext

    runtime = tmp_path / "hooks"
    runtime.mkdir()
    flatten_into_single_runtime_directory(runtime)
    with tempfile.TemporaryDirectory(dir="/tmp") as sockets:
        server = RecordingHerdrSocketServer(Path(sockets) / "herdr.sock")
        contexts = []
        try:
            for pane in ["first", "second"]:
                identifier = str(uuid4())
                context = ClientContext(
                    tmp_path / "client-context",
                    {
                        "HERDR_ENV": "1",
                        "HERDR_PANE_ID": pane,
                        "HERDR_SOCKET_PATH": str(server.socket_path),
                        "AGENT_INTERACTIVE_PREFERENCES_PATH": "instructions.md",
                    },
                    {"developer_instructions": "INSTRUCTIONS=" + pane},
                )
                contexts.append(context)
                context.claim(identifier)
                result = run_flattened_hook(
                    runtime,
                    "session-start-dispatcher.py",
                    {
                        "hook_event_name": "SessionStart",
                        "source": source,
                        "session_id": identifier,
                        "transcript_path": str(tmp_path / "transcript.jsonl"),
                    },
                    {
                        "CODEX_HOME": str(tmp_path),
                        "HOME": str(tmp_path),
                        "DOTFILES_CODEX_SHARED_SERVER": "1",
                        "HERDR_PANE_ID": "wrong",
                        "CLAWDE_AGENT_NAME": "wrong",
                        "CODEX_THREAD_ID": "wrong",
                    },
                    extra_arguments=("--surface=codex",),
                    working_directory=tmp_path,
                )
                assert result.returncode == 0, result.stderr
                content = json.loads(result.stdout)["hookSpecificOutput"][
                    "additionalContext"
                ]
                assert "INSTRUCTIONS=" + pane in content
                assert "Servant: " in content
                reported = server.received_requests[-1]["params"]
                assert reported["pane_id"] == pane
                assert reported["agent_session_id"] == identifier
            assert len(server.received_requests) == 2
        finally:
            for context in contexts:
                context.close()
            server.close()
