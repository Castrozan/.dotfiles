import hashlib
import re
from pathlib import Path

import yaml

from run_evals_worktree_and_environment import REPO_ROOT

HUMANIZE_RECOVERY_SUITE_PATH = Path(
    "agent-harness/agent-instructions/skills/humanize/__tests__/evals/reader_recovery.yaml"
)
JUDGE_CALIBRATION_PATH = Path(
    "agent-harness/quality/evaluations/calibration/judge_calibration.yaml"
)
HUMANIZE_EVIDENCE_RUNNER_COMPONENTS = (
    "run_evals_ab.py",
    "run_evals_assertions.py",
    "run_evals_config_loader.py",
    "run_evals_judge.py",
    "run_evals_significance.py",
    "run_evals_subject_port.py",
    "run_evals_test_runner.py",
    "node-provider-runtime/package.json",
    "node-provider-runtime/package-lock.json",
    "node-provider-runtime/provider-adapters.mjs",
    "node-provider-runtime/provider-runners.mjs",
    "node-provider-runtime/provider-runtime.mjs",
)


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
        digest.update(
            instruction_wording(path.read_text(encoding="utf-8")).encode("utf-8")
        )
        digest.update(b"\0")
    return digest.hexdigest()


def evaluation_suite_paths(repo_root: Path) -> set[Path]:
    evaluation_root = repo_root / "agent-harness" / "quality" / "evaluations"
    paths = set((evaluation_root / "evals").glob("*.yaml"))
    paths.update((evaluation_root / "calibration").glob("*.yaml"))
    paths.update(
        repo_root.glob(
            "agent-harness/agent-instructions/skills/*/__tests__/evals/*.yaml"
        )
    )
    return paths


def evaluation_runner_paths(repo_root: Path) -> set[Path]:
    evaluation_root = repo_root / "agent-harness" / "quality" / "evaluations"
    paths = set(evaluation_root.glob("run_evals_*.py"))
    for runner_component in (
        "run-evals.py",
        "agent-evaluations-home-manager.nix",
        "node-provider-runtime-package.nix",
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
        for path in (evaluation_root / "evals").glob("*.yaml")
        if path.name != "settings.yaml"
    }
    for path in repo_root.glob(
        "agent-harness/agent-instructions/skills/*/__tests__/evals/*.yaml"
    ):
        if path.name != "settings.yaml":
            categories.add(f"skills/{path.parent.parent.parent.name}/{path.stem}")
    return categories


def humanize_evidence_runner_paths(repo_root: Path) -> set[Path]:
    evaluation_root = repo_root / "agent-harness" / "quality" / "evaluations"
    return {
        path
        for relative_path in HUMANIZE_EVIDENCE_RUNNER_COMPONENTS
        if (path := evaluation_root / relative_path).is_file()
    }


def referenced_instruction_paths(repo_root: Path, suite_paths: set[Path]) -> set[Path]:
    paths = set()
    for suite_path in suite_paths:
        document = yaml.safe_load(suite_path.read_text()) or {}
        for test in document.get("tests", []):
            candidates = [test.get("skill_path")]
            candidates.extend(test.get("extra_skill_paths") or [])
            if test.get("agent"):
                candidates.append(
                    f"agent-harness/agent-instructions/skills/{test['agent']}/SKILL.md"
                )
            for candidate in candidates:
                if candidate:
                    paths.add(repo_root / candidate)
    return {path for path in paths if path.is_file()}


def evaluation_fingerprints(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    suite_paths = evaluation_suite_paths(repo_root)
    instruction_paths = referenced_instruction_paths(repo_root, suite_paths)
    return {
        "suite": digest_paths(
            repo_root, suite_paths | evaluation_runner_paths(repo_root)
        ),
        "instructions": digest_instruction_paths(repo_root, instruction_paths),
    }


def humanize_recovery_fingerprints(
    repo_root: Path = REPO_ROOT,
) -> dict[str, str]:
    suite_paths = {
        repo_root / HUMANIZE_RECOVERY_SUITE_PATH,
        repo_root / JUDGE_CALIBRATION_PATH,
    }
    instruction_paths = referenced_instruction_paths(repo_root, suite_paths)
    return {
        "suite": digest_paths(
            repo_root, suite_paths | humanize_evidence_runner_paths(repo_root)
        ),
        "instructions": digest_instruction_paths(repo_root, instruction_paths),
    }
