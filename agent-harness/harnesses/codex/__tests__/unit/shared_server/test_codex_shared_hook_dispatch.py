import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import pytest

from codex_client_context import ClientContext


@pytest.mark.parametrize(
    "surface,expected",
    [("codex", "correct"), ("claude", "original"), ("opencode", "original")],
)
def test_common_dispatcher_restores_only_codex_context(tmp_path, surface, expected):
    harness_root = Path(__file__).resolve().parents[5]
    shared_modules = harness_root / "harnesses/codex/scripts/shared_server"
    common_modules = harness_root / "hooks/runtime/common"
    identifier = str(uuid4())
    context = ClientContext(tmp_path / "client-context", {"HERDR_PANE_ID": "correct"})
    context.claim(identifier)
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import os; from hook_dispatch import read_hook_input_or_exit; read_hook_input_or_exit(); print(os.environ.get('HERDR_PANE_ID'))",
                "--surface=" + surface,
            ],
            input=json.dumps({"session_id": identifier}),
            text=True,
            capture_output=True,
            env={
                **os.environ,
                "CODEX_HOME": str(tmp_path),
                "DOTFILES_CODEX_SHARED_SERVER": "1",
                "HERDR_PANE_ID": "original",
                "PYTHONPATH": os.pathsep.join(
                    map(str, [shared_modules, common_modules])
                ),
            },
            timeout=5,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == expected
    finally:
        context.close()
