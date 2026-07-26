from render_quality_metrics import (
    build_quality_metrics,
    count_hook_entry_points,
    count_scenario_definitions,
    is_hook_entry_point_module,
)


def write_empty_file(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")


class TestScenarioCountingReachesNestedSuites:
    def test_counts_scenarios_nested_inside_suite_directories(self, tmp_path):
        write_empty_file(tmp_path / "flat-scenario.yaml")
        write_empty_file(tmp_path / "skill-discovery/first.yaml")
        write_empty_file(tmp_path / "skill-discovery/second.yaml")

        assert count_scenario_definitions(tmp_path) == 3

    def test_ignores_files_that_are_not_scenario_definitions(self, tmp_path):
        write_empty_file(tmp_path / "scenario.yaml")
        write_empty_file(tmp_path / "README.md")
        write_empty_file(tmp_path / "helper.py")

        assert count_scenario_definitions(tmp_path) == 1


class TestHookEntryPointsAreDistinguishedFromHelperModules:
    def test_hyphenated_module_is_an_entry_point(self, tmp_path):
        assert is_hook_entry_point_module(tmp_path / "end-of-turn-format-guard.py")

    def test_underscored_module_is_a_helper_not_an_entry_point(self, tmp_path):
        assert not is_hook_entry_point_module(
            tmp_path / "end_of_turn_reply_template_rules.py"
        )

    def test_counts_flat_entry_points_and_nested_hook_directories_together(
        self, tmp_path
    ):
        write_empty_file(tmp_path / "auto-format.py")
        write_empty_file(tmp_path / "formatter_table_by_extension.py")
        write_empty_file(tmp_path / "line-count/hook.py")
        write_empty_file(tmp_path / "common/shared.py")

        assert count_hook_entry_points(tmp_path) == 2


class TestPublishedMetricsContractWithTheReportsFrontend:
    def test_exposes_every_field_the_quality_page_renders(self):
        metrics = build_quality_metrics()

        assert set(metrics) == {
            "generatedAt",
            "generatedCommit",
            "staticEvals",
            "integrationScenarioCount",
            "endToEndScenarioCount",
            "coreRules",
            "hooks",
        }
        assert set(metrics["staticEvals"]) == {
            "totalTests",
            "passedTests",
            "passRate",
            "suiteCount",
            "categoryCount",
            "recordedAt",
            "recordedCommit",
        }
        assert set(metrics["coreRules"]) == {"lineCount", "ruleBlockCount"}
        assert set(metrics["hooks"]) == {"wiredEvents", "entryPointCount"}

    def test_every_published_count_is_derived_and_non_zero(self):
        metrics = build_quality_metrics()

        assert metrics["staticEvals"]["totalTests"] > 0
        assert metrics["integrationScenarioCount"] > 0
        assert metrics["endToEndScenarioCount"] > 0
        assert metrics["coreRules"]["lineCount"] > 0
        assert metrics["coreRules"]["ruleBlockCount"] > 0
        assert metrics["hooks"]["entryPointCount"] > 0

    def test_pass_rate_is_a_fraction_not_a_percentage(self):
        assert 0 < build_quality_metrics()["staticEvals"]["passRate"] <= 1
