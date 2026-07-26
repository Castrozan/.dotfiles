#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

INSTRUCTION_LOADING_EXPERIMENT_RELATIVE_PATH = (
    "agents/__tests__/instruction-loading-experiment.json"
)


def read_recorded_experiment(repository_root: Path) -> dict:
    experiment_path = repository_root / INSTRUCTION_LOADING_EXPERIMENT_RELATIVE_PATH
    return json.loads(experiment_path.read_text())


def build_contracted_category(recorded_category_name: str, measurements: dict) -> dict:
    return {
        "category": recorded_category_name.replace("_", "-"),
        "pairedTests": measurements["paired_tests"],
        "passRateWithInstructions": measurements["pass_rate_with_instructions"],
        "passRateWithoutInstructions": measurements["pass_rate_without_instructions"],
        "delta": measurements["delta"],
        "instructionsOnlyWins": measurements["instructions_only_wins"],
        "controlOnlyWins": measurements["control_only_wins"],
        "exactPValue": measurements["mcnemar_exact_p_value"],
        "significant": measurements["significant"],
    }


def build_instruction_loading_experiment(repository_root: Path) -> dict:
    experiment = read_recorded_experiment(repository_root)
    return {
        "recordedAt": experiment["generated_at"],
        "recordedCommit": experiment["git_commit"],
        "significanceAlpha": experiment["significance_alpha"],
        "categories": [
            build_contracted_category(recorded_category_name, measurements)
            for recorded_category_name, measurements in experiment["categories"].items()
        ],
    }
