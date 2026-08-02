import json
import os
import pathlib
import shutil
import site
import subprocess


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
PYRIGHT_TARGETS = (
    REPO_ROOT / "agents/hooks/__tests__/conftest.py",
    REPO_ROOT / "agents/hooks/post-tool-use/auto_format_handler.py",
    REPO_ROOT / "agents/hooks/post-tool-use/post-tool-use-dispatcher.py",
)
EXPECTED_EXTRA_PATHS = {
    "agents/hooks",
    "agents/hooks/__tests__",
    "agents/hooks/__tests__/e2e",
    "agents/hooks/__tests__/integration",
    "agents/hooks/__tests__/unit",
    "agents/hooks/common",
    "agents/hooks/common/human_facing_reply",
    "agents/hooks/lint",
    "agents/hooks/post-tool-use",
    "agents/hooks/post-tool-use/instructions-skill-invocation",
    "agents/hooks/post-tool-use/line-count",
    "agents/hooks/post-tool-use/skill-invocation-marker",
    "agents/hooks/pre-tool-use",
    "agents/hooks/pre-tool-use/agent-instruction-file-authoring-router",
    "agents/hooks/pre-tool-use/background-bash-anti-pattern-validator",
    "agents/hooks/pre-tool-use/blocked-skill-invocation-guard",
    "agents/hooks/pre-tool-use/codex-sandbox-downgrade-guard",
    "agents/hooks/pre-tool-use/common",
    "agents/hooks/pre-tool-use/documentation-authoring-router",
    "agents/hooks/pre-tool-use/monitor-streaming-pattern-validator",
    "agents/hooks/pre-tool-use/prohibited-command-guard",
    "agents/hooks/pre-tool-use/prohibited-words-guard",
    "agents/hooks/pre-tool-use/subagent-budget-guard",
    "agents/hooks/pre-tool-use/url-to-skill-router",
    "agents/hooks/pre-tool-use/workspace-directory-injector",
    "agents/hooks/pre-tool-use/worktree-location-guard",
    "agents/hooks/session-start",
    "agents/hooks/stop",
    "agents/hooks/user-prompt-submit",
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
