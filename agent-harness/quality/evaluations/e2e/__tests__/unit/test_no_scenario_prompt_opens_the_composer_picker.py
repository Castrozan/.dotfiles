from e2e_scenario_steps import scenario_steps, step_requests_compaction
from e2e_workspace import SCENARIOS_DIR, discover_scenario_files, load_scenario

COMPOSER_PICKER_TRIGGER = "@"


def test_no_scenario_prompt_types_a_composer_picker_trigger():
    for scenario_file in discover_scenario_files(SCENARIOS_DIR):
        scenario = load_scenario(scenario_file)
        for step in scenario_steps(scenario):
            if step_requests_compaction(step):
                continue
            assert COMPOSER_PICKER_TRIGGER not in step, (
                f"{scenario['name']} types '{COMPOSER_PICKER_TRIGGER}' into the "
                "composer, which opens the mention picker, so the Enter that follows "
                "selects the highlighted entry instead of submitting the prompt. The "
                "agent never receives the request and the scenario grades an untouched "
                "workspace. Seed file content may contain it; only typed prompts may "
                "not."
            )
