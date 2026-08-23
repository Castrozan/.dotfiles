from e2e_assertions_naming import check_workspace_file_descriptive_names_assertion
from e2e_workspace import SCENARIOS_DIR, discover_scenario_files, load_scenario


def test_every_seeded_file_graded_for_descriptive_names_already_passes(tmp_path):
    for scenario_file in discover_scenario_files(SCENARIOS_DIR):
        scenario = load_scenario(scenario_file)
        graded_paths = scenario.get("assertions", {}).get(
            "workspace_file_descriptive_names", []
        )
        if not graded_paths:
            continue

        seeded_files_by_path = {
            file_definition["path"]: file_definition["content"]
            for file_definition in scenario.get("setup", {}).get("files", [])
        }
        seed_workspace = tmp_path / scenario_file.stem

        for graded_path in graded_paths:
            if graded_path not in seeded_files_by_path:
                continue
            seeded_file_path = seed_workspace / graded_path
            seeded_file_path.parent.mkdir(parents=True, exist_ok=True)
            seeded_file_path.write_text(seeded_files_by_path[graded_path])

            result = check_workspace_file_descriptive_names_assertion(
                seed_workspace, graded_path
            )
            assert result.passed, (
                f"{scenario['name']} seeds {graded_path} with content that already "
                f"fails the descriptive-names check it grades: {result.detail}"
            )
