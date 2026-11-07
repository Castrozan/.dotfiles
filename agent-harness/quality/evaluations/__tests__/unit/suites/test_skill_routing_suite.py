import re
from pathlib import Path

import pytest
import yaml
from instructions.instruction_surface_scanner import (
    frontmatter_key_values,
    public_skill_definition_path,
)

EVAL_HARNESS_ROOT = Path(__file__).resolve().parents[3]
SKILLS_ROOT = Path(__file__).resolve().parents[5] / "agent-instructions/skills"
SKILL_ROUTING_SUITE = EVAL_HARNESS_ROOT / "evals" / "skill_routing.yaml"
ROUTER_CATALOG_ENTRY = re.compile(
    r"^([a-z][a-z0-9-]*) - (.+)$",
    re.MULTILINE,
)

ROUTER_CATALOGS = [
    (SKILL_ROUTING_SUITE, "shared_system_prompt", 10),
]

DEPLOYED_SKILLS_WITHOUT_A_SAME_NAMED_SOURCE = {"all-skills", "wellput"}
INTERACTIVE_SKILL_CATALOG = (
    Path(__file__).resolve().parents[5]
    / "agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix"
)
DEFAULT_INTERACTIVE_SKILL_LIST = re.compile(
    r"defaultInteractiveSkillNames = \[(.*?)\];", re.DOTALL
)


def load_skill_routing_config():
    return yaml.safe_load(SKILL_ROUTING_SUITE.read_text())


def router_catalog_skill_names(config, prompt_key):
    return [name for name, _ in ROUTER_CATALOG_ENTRY.findall(config[prompt_key])]


def router_catalog_descriptions(config, prompt_key):
    return dict(ROUTER_CATALOG_ENTRY.findall(config[prompt_key]))


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
        if name not in DEPLOYED_SKILLS_WITHOUT_A_SAME_NAMED_SOURCE
        and public_skill_definition_path(name) is None
    ]
    assert not missing, (
        f"{config_path.name} offers skills that no longer exist: {missing}; a routing "
        f"test can never pass once its expected answer has been deleted or renamed"
    )


def deployed_default_skill_names():
    skill_list = DEFAULT_INTERACTIVE_SKILL_LIST.search(
        INTERACTIVE_SKILL_CATALOG.read_text()
    )
    assert skill_list, "interactive-agent-skills.nix lost defaultInteractiveSkillNames"
    return set(re.findall(r'"([a-z][a-z0-9-]*)"', skill_list.group(1)))


def test_router_catalog_offers_exactly_the_deployed_default_skills():
    catalog = set(
        router_catalog_skill_names(load_skill_routing_config(), "shared_system_prompt")
    )
    deployed = deployed_default_skill_names() | {"all-skills"}
    assert catalog == deployed, (
        "the routing catalog must mirror the skills every session loads; "
        f"missing: {sorted(deployed - catalog)}, not deployed: {sorted(catalog - deployed)}"
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


@pytest.mark.parametrize("config_path,prompt_key,minimum", ROUTER_CATALOGS)
def test_router_catalog_uses_current_skill_descriptions(
    config_path, prompt_key, minimum
):
    config = yaml.safe_load(config_path.read_text())
    catalog = router_catalog_descriptions(config, prompt_key)
    assert len(catalog) >= minimum
    mismatches = {}
    for name, routed_description in catalog.items():
        skill_file = public_skill_definition_path(name)
        if skill_file is None:
            continue
        actual_description = (frontmatter_key_values(skill_file.read_text()) or {}).get(
            "description"
        )
        if actual_description != routed_description:
            mismatches[name] = {
                "catalog": routed_description,
                "skill": actual_description,
            }
    assert not mismatches, (
        f"the routing catalog carries stale skill descriptions: {mismatches}"
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
