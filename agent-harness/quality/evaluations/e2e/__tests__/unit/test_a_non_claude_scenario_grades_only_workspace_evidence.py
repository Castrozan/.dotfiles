from e2e_harness_profiles import DEFAULT_HARNESS_NAME
from e2e_workspace import SCENARIOS_DIR, discover_scenario_files, load_scenario

WORKSPACE_DERIVED_ASSERTION_KEYS = {
    "workspace_file_no_comments",
    "workspace_file_descriptive_names",
    "file_changed",
    "workspace_formatted",
}


def test_only_claude_scenarios_grade_evidence_parsed_from_the_terminal_trace():
    for scenario_file in discover_scenario_files(SCENARIOS_DIR):
        scenario = load_scenario(scenario_file)
        if scenario.get("harness", DEFAULT_HARNESS_NAME) == DEFAULT_HARNESS_NAME:
            continue
        trace_derived_keys = (
            set(scenario.get("assertions", {})) - WORKSPACE_DERIVED_ASSERTION_KEYS
        )
        assert trace_derived_keys == set(), (
            f"{scenario['name']} runs on {scenario['harness']} but grades "
            f"{sorted(trace_derived_keys)}, which the trace parser reads from the "
            "Claude transcript render"
        )
        assert "minimum_experience_score" not in scenario, scenario["name"]
