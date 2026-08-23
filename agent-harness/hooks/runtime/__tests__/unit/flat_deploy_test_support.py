import json
import shutil
import subprocess
import sys
from pathlib import Path

from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS

HOOKS_ROOT = Path(__file__).resolve().parents[2]

DEPLOYED_HOOK_SCRIPT_SUFFIXES = (".py", ".sh", ".md")
DIRECTORIES_EXCLUDED_FROM_DEPLOY = ("__pycache__", "__tests__")

INTERACTIVE_ENV_VAR = "AGENT_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENV_MARKER = "CLAWDE_AGENT_NAME"

DOMAIN_DIRECTORY_SUBSTITUTIONS = {
    "@servantsDomainDirectory@": HOOKS_ROOT.parents[1] / "servants",
    "@clawdeWorkspaceDomainDirectory@": HOOKS_ROOT.parents[1]
    / "harnesses"
    / "clawde"
    / "scripts",
}


def every_deployed_hook_script():
    return [
        candidate
        for candidate in HOOKS_ROOT.rglob("*")
        if candidate.is_file()
        and candidate.suffix in DEPLOYED_HOOK_SCRIPT_SUFFIXES
        and not any(
            excluded in candidate.parts for excluded in DIRECTORIES_EXCLUDED_FROM_DEPLOY
        )
    ]


def flatten_into_single_runtime_directory(directory, source_files=None):
    """Flatten the hook tree, then apply the substitutions the nix builder applies.

    flat-hook-scripts-directory.nix rewrites each domain placeholder to the store
    path holding that domain. A flatten that skipped one would deploy a script that
    can never import the domain it needs, and the dispatcher swallows a failed
    handler, so the test would read that silence as a pass.
    """
    for source_file in (
        source_files if source_files is not None else every_deployed_hook_script()
    ):
        deployed_file = directory / source_file.name
        shutil.copy(source_file, deployed_file)
        deployed_text = deployed_file.read_text(encoding="utf-8", errors="replace")
        substituted_text = deployed_text
        for placeholder, domain_directory in DOMAIN_DIRECTORY_SUBSTITUTIONS.items():
            substituted_text = substituted_text.replace(
                placeholder, str(domain_directory)
            )
        if substituted_text == deployed_text:
            continue
        deployed_file.write_text(substituted_text, encoding="utf-8")


def run_flattened_hook(
    directory,
    hook_filename,
    payload,
    environment,
    extra_arguments=(),
    working_directory=None,
):
    return subprocess.run(
        [sys.executable, str(directory / hook_filename), *extra_arguments],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
        env=environment,
        cwd=working_directory,
    )
