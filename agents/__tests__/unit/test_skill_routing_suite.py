import re
from pathlib import Path

import pytest
import yaml

EVAL_HARNESS_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = (
    Path(__file__).resolve().parents[3]
    / "agent-harness"
    / "agent-instructions"
    / "skills"
)
SKILL_ROUTING_SUITE = EVAL_HARNESS_ROOT / "evals" / "skill_routing.yaml"
ROUTER_CATALOG_ENTRY = re.compile(r"^([a-z][a-z0-9-]*) - ", re.MULTILINE)

ROUTER_CATALOGS = [
    (SKILL_ROUTING_SUITE, "shared_system_prompt", 10),
]

GENERATED_SKILL_NAMES = {"all-skills"}


def load_skill_routing_config():
    return yaml.safe_load(SKILL_ROUTING_SUITE.read_text())


def router_catalog_skill_names(config, prompt_key):
    return ROUTER_CATALOG_ENTRY.findall(config[prompt_key])


@pytest.mark.parametrize("config_path,prompt_key,minimum", ROUTER_CATALOGS)
def test_every_skill_in_a_router_catalog_exists_on_disk(
    config_path, prompt_key, minimum
):
    config = yaml.safe_load(config_path.read_text())
    catalog = router_catalog_skill_names(config, prompt_key)
    assert len(catalog) >= minimum
    missing = [
        name
        for name in catalog
        if name not in GENERATED_SKILL_NAMES and not (SKILLS_ROOT / name).is_dir()
    ]
    assert not missing, (
        f"{config_path.name} offers skills that no longer exist: {missing}; a routing "
        f"test can never pass once its expected answer has been deleted or renamed"
    )


@pytest.mark.parametrize("config_path,prompt_key,minimum", ROUTER_CATALOGS)
def test_every_expected_routing_answer_is_offered_by_its_catalog(
    config_path, prompt_key, minimum
):
    config = yaml.safe_load(config_path.read_text())
    catalog = set(router_catalog_skill_names(config, prompt_key))
    unofferable = sorted(
        {
            expected
            for test in config["tests"]
            for expected in test["assertions"].get("output_equals", [])
            if expected not in catalog
        }
    )
    assert not unofferable, (
        f"{config_path.name} routing tests expect an answer the router prompt never "
        f"offers: {unofferable}; the test grades the catalog, not the model"
    )


def test_skill_routing_grades_by_exact_match_not_substring():
    tests = yaml.safe_load(SKILL_ROUTING_SUITE.read_text())["tests"]
    assert tests
    for test in tests:
        assertions = test["assertions"]
        assert "output_equals" in assertions, (
            f"{test['name']} lost its exact-match grading"
        )
        assert "output_contains_any" not in assertions, (
            f"{test['name']} still grades by substring"
        )
        assert "output_contains" not in assertions
        assert "output_not_contains" not in assertions
        assert len(assertions["output_equals"]) >= 1
