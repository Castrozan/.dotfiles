import re
from pathlib import Path

import yaml

SKILL_ROUTING_CONFIG = (
    Path(__file__).resolve().parents[2] / "config" / "skill_routing.yaml"
)
SKILLS_ROOT = Path(__file__).resolve().parents[3] / "skills"
ROUTER_CATALOG_ENTRY = re.compile(r"^([a-z][a-z0-9-]*) - ", re.MULTILINE)


def load_skill_routing_config():
    return yaml.safe_load(SKILL_ROUTING_CONFIG.read_text())


def router_catalog_skill_names(config):
    return ROUTER_CATALOG_ENTRY.findall(config["shared_system_prompt"])


def test_every_skill_in_the_router_catalog_exists_on_disk():
    catalog = router_catalog_skill_names(load_skill_routing_config())
    assert len(catalog) > 10
    missing = [name for name in catalog if not (SKILLS_ROOT / name).is_dir()]
    assert not missing, (
        f"the router catalog offers skills that no longer exist: {missing}; a routing "
        f"test can never pass once its expected answer has been deleted or renamed"
    )


def test_every_expected_routing_answer_is_offered_by_the_catalog():
    config = load_skill_routing_config()
    catalog = set(router_catalog_skill_names(config))
    unofferable = sorted(
        {
            expected
            for test in config["tests"]
            for expected in test["assertions"]["output_equals"]
            if expected not in catalog
        }
    )
    assert not unofferable, (
        f"these routing tests expect an answer the router prompt never offers: "
        f"{unofferable}; the test grades the catalog, not the model"
    )


def test_skill_routing_grades_by_exact_match_not_substring():
    tests = yaml.safe_load(SKILL_ROUTING_CONFIG.read_text())["tests"]
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
