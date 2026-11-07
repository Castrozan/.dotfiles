import hashlib
import json
import re
from pathlib import Path

from instructions.instruction_surface_scanner import public_skill_definition_path
from instructions.reply_format_instructions import (
    REPLY_FORMAT_CONFIGURATION_PATH,
    REPLY_FORMAT_PLACEHOLDER,
    expand_reply_format_instructions,
)

import yaml

from runner.run_evals_worktree_and_environment import REPO_ROOT



YAML_FILE_PATTERN = "*.yaml"
MARKDOWN_EMPHASIS_PATTERN = re.compile(r"[*_`]+")


def digest_paths(repo_root: Path, paths: set[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        relative_path = path.relative_to(repo_root)
        digest.update(str(relative_path).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def instruction_wording(text: str) -> str:
    """Reduce instruction prose to the wording a measurement actually depends on.

    Line wrapping, letter case, and markdown emphasis carry no behavioral
    meaning in an instruction surface, and this repository rewraps those files
    to a fixed column constantly. Hashing them raw made a reflow or a capital
    letter as invalidating as a rewritten rule, which forced a full A/B run to
    re-authorize evidence that no model output could have differed on.
    """
    return " ".join(MARKDOWN_EMPHASIS_PATTERN.sub("", text).lower().split())


def digest_instruction_paths(repo_root: Path, paths: set[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        relative_path = path.relative_to(repo_root)
        digest.update(str(relative_path).encode())
        digest.update(b"\0")
        text = path.read_text(encoding="utf-8")
        if REPLY_FORMAT_PLACEHOLDER in text:
            configuration = json.loads(
                (repo_root / REPLY_FORMAT_CONFIGURATION_PATH).read_text()
            )
            text = expand_reply_format_instructions(text, configuration)
        digest.update(instruction_wording(text).encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def evaluation_suite_paths(repo_root: Path) -> set[Path]:
    evaluation_root = repo_root / "agent-harness" / "quality" / "evaluations"
    paths = set((evaluation_root / "evals").rglob(YAML_FILE_PATTERN))
    paths.update((evaluation_root / "calibration").glob(YAML_FILE_PATTERN))
    paths.update(
        repo_root.glob(
            "agent-harness/agent-instructions/skills/**/__tests__/evals/*.yaml"
        )
    )
    return paths


def evaluation_runner_paths(repo_root: Path) -> set[Path]:
    evaluation_root = repo_root / "agent-harness" / "quality" / "evaluations"
    paths = set((evaluation_root / "runner").rglob("run_evals_*.py"))
    paths.update((evaluation_root / "reporting").glob("run_evals_*.py"))
    for runner_component in (
        "instructions/instruction_surface_scanner.py",
        "instructions/reply_format_instructions.py",
        "run-evals.py",
        "agent-evaluations-home-manager.nix",
        "node-provider-runtime/package.nix",
        "node-provider-runtime/package.json",
        "node-provider-runtime/package-lock.json",
    ):
        component_path = evaluation_root / runner_component
        if component_path.is_file():
            paths.add(component_path)
    paths.update(
        path
        for path in (evaluation_root / "node-provider-runtime").glob("*.mjs")
        if not path.name.endswith(".test.mjs")
    )
    return paths


def evaluation_category_names(repo_root: Path = REPO_ROOT) -> set[str]:
    evaluation_root = repo_root / "agent-harness" / "quality" / "evaluations"
    categories = {
        path.stem
        for path in (evaluation_root / "evals").rglob(YAML_FILE_PATTERN)
        if path.name != "settings.yaml"
    }
    for path in repo_root.glob(
        "agent-harness/agent-instructions/skills/**/__tests__/evals/*.yaml"
    ):
        if path.name != "settings.yaml":
            categories.add(f"skills/{path.parent.parent.parent.name}/{path.stem}")
    return categories


def referenced_instruction_paths(repo_root: Path, suite_paths: set[Path]) -> set[Path]:
    paths = set()
    for suite_path in suite_paths:
        document = yaml.safe_load(suite_path.read_text()) or {}
        for test in document.get("tests", []):
            paths.update(_instruction_paths_for_test(repo_root, test))
    return {path for path in paths if path.is_file()}


def _instruction_paths_for_test(repo_root: Path, test: dict) -> set[Path]:
    candidates = [test.get("skill_path")]
    candidates.extend(test.get("extra_skill_paths") or [])
    if test.get("agent"):
        candidates.append(public_skill_definition_path(test["agent"], repo_root))
    return {repo_root / candidate for candidate in candidates if candidate}


def evaluation_fingerprints(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    suite_paths = evaluation_suite_paths(repo_root)
    instruction_paths = referenced_instruction_paths(repo_root, suite_paths)
    return {
        "suite": digest_paths(
            repo_root, suite_paths | evaluation_runner_paths(repo_root)
        ),
        "instructions": digest_instruction_paths(repo_root, instruction_paths),
    }

