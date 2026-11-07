import re
from pathlib import Path

from evaluation_suite_support import load_suite_cases
from instructions.instruction_surface_scanner import (
    frontmatter_key_values,
    public_skill_definition_path,
)

DEPLOYED_SKILLS_WITHOUT_A_SAME_NAMED_SOURCE = {"all-skills", "wellput"}
MINIMUM_CATALOG_SKILLS = 10
INTERACTIVE_SKILL_CATALOG = (
    Path(__file__).resolve().parents[5]
    / "agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix"
)
DEFAULT_INTERACTIVE_SKILL_LIST = re.compile(
    r"defaultInteractiveSkillNames = \[(.*?)\];", re.DOTALL
)
ROUTER_CATALOG_ENTRY = re.compile(r"^([a-z][a-z0-9-]*) - (.+)$", re.MULTILINE)


def routing_cases():
    return load_suite_cases("skill_routing")


def router_catalog_descriptions():
    prompts = {case["system_prompt"] for case in routing_cases()}
    assert len(prompts) == 1, "every routing case must share one router catalog"
    return dict(ROUTER_CATALOG_ENTRY.findall(prompts.pop()))


def deployed_default_skill_names():
    skill_list = DEFAULT_INTERACTIVE_SKILL_LIST.search(
        INTERACTIVE_SKILL_CATALOG.read_text()
    )
    assert skill_list, "interactive-agent-skills.nix lost defaultInteractiveSkillNames"
    return set(re.findall(r'"([a-z][a-z0-9-]*)"', skill_list.group(1)))


def test_every_skill_in_the_router_catalog_exists_on_disk():
    catalog = router_catalog_descriptions()
    assert len(catalog) >= MINIMUM_CATALOG_SKILLS
    missing = [
        name
        for name in catalog
        if name not in DEPLOYED_SKILLS_WITHOUT_A_SAME_NAMED_SOURCE
        and public_skill_definition_path(name) is None
    ]
    assert not missing, (
        f"the routing catalog offers skills that no longer exist: {missing}; a "
        f"routing case can never pass once its expected answer has been deleted or "
        f"renamed"
    )


def test_router_catalog_offers_exactly_the_deployed_default_skills():
    catalog = set(router_catalog_descriptions())
    deployed = deployed_default_skill_names() | {"all-skills"}
    assert catalog == deployed, (
        "the routing catalog must mirror the skills every session loads; "
        f"missing: {sorted(deployed - catalog)}, not deployed: {sorted(catalog - deployed)}"
    )


def test_every_expected_routing_answer_is_offered_by_the_catalog():
    catalog = set(router_catalog_descriptions())
    unofferable = sorted(
        {
            expected
            for case in routing_cases()
            for expected in case["assercoes"]["igual"]
            if expected not in catalog
        }
    )
    assert not unofferable, (
        f"routing cases expect an answer the router prompt never offers: "
        f"{unofferable}; the case grades the catalog, not the model"
    )


def test_router_catalog_uses_current_skill_descriptions():
    mismatches = {}
    for name, routed_description in router_catalog_descriptions().items():
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


def test_skill_routing_grades_by_exact_match_only():
    cases = routing_cases()
    assert cases
    for case in cases:
        assert set(case["assercoes"]) == {"igual"}, (
            f"{case['nome']} must grade by exact match alone"
        )
        assert case["assercoes"]["igual"]
