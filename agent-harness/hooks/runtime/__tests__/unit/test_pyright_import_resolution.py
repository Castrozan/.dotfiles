import json
import os
import pathlib
import shutil
import site
import subprocess


REPO_ROOT = pathlib.Path(__file__).resolve().parents[5]
PYRIGHT_TARGETS = (
    REPO_ROOT / "agent-harness/hooks/runtime/__tests__/conftest.py",
    REPO_ROOT / "agent-harness/hooks/runtime/post-tool-use/auto_format_handler.py",
    REPO_ROOT / "agent-harness/hooks/runtime/post-tool-use/post-tool-use-dispatcher.py",
)
EXPECTED_EXTRA_PATHS = {
    "agent-harness/hooks/runtime",
    "agent-harness/hooks/runtime/__tests__",
    "agent-harness/hooks/runtime/__tests__/e2e",
    "agent-harness/hooks/runtime/__tests__/integration",
    "agent-harness/hooks/runtime/__tests__/unit",
    "agent-harness/hooks/runtime/common",
    "agent-harness/hooks/runtime/common/human_facing_reply",
    "agent-harness/hooks/runtime/post-tool-use",
    "agent-harness/hooks/runtime/post-tool-use/instructions-skill-invocation",
    "agent-harness/hooks/runtime/post-tool-use/line-count",
    "agent-harness/hooks/runtime/post-tool-use/skill-invocation-marker",
    "agent-harness/hooks/runtime/pre-tool-use",
    "agent-harness/hooks/runtime/pre-tool-use/agent-instruction-file-authoring-router",
    "agent-harness/hooks/runtime/pre-tool-use/background-bash-anti-pattern-validator",
    "agent-harness/hooks/runtime/pre-tool-use/blocked-skill-invocation-guard",
    "agent-harness/hooks/runtime/pre-tool-use/codex-sandbox-downgrade-guard",
    "agent-harness/hooks/runtime/pre-tool-use/common",
    "agent-harness/hooks/runtime/pre-tool-use/documentation-authoring-router",
    "agent-harness/hooks/runtime/pre-tool-use/monitor-streaming-pattern-validator",
    "agent-harness/hooks/runtime/pre-tool-use/prohibited-command-guard",
    "agent-harness/hooks/runtime/pre-tool-use/prohibited-words-guard",
    "agent-harness/hooks/runtime/pre-tool-use/subagent-budget-guard",
    "agent-harness/hooks/runtime/pre-tool-use/url-to-skill-router",
    "agent-harness/hooks/runtime/pre-tool-use/workspace-directory-injector",
    "agent-harness/hooks/runtime/pre-tool-use/worktree-location-guard",
    "agent-harness/hooks/runtime/session-start",
    "agent-harness/hooks/runtime/stop",
}


def test_pyright_resolves_hook_imports_and_test_dependencies():
    pyright_command = shutil.which("pyright")
    assert pyright_command is not None, "pyright must be available for hook diagnostics"
    python_package_paths = site.getsitepackages()
    environment = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(python_package_paths),
    }
    completed = subprocess.run(
        [pyright_command, *(str(target) for target in PYRIGHT_TARGETS)],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr

    pyright_configuration_path = REPO_ROOT / "pyrightconfig.json"
    pyright_configuration = json.loads(
        pyright_configuration_path.read_text(encoding="utf-8")
    )
    assert EXPECTED_EXTRA_PATHS <= set(pyright_configuration["extraPaths"])
