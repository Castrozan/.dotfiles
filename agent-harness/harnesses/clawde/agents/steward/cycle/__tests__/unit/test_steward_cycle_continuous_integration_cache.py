import json

from cycle_observation import continuous_integration_for
from cycle_records import revision_record_path, write_record
from test_steward_cycle_records_and_worker import configuration_in

REVISION = "a" * 40


class RerunPassingForgeRunner:
    def __init__(self):
        self.queries = 0

    def run_capturing(self, arguments, directory, timeout_seconds):
        self.queries += 1
        runs = [
            {
                "workflowName": "deploy reports",
                "headSha": REVISION,
                "status": "completed",
                "conclusion": "success",
                "url": "https://example.test/runs/2",
            },
            {
                "workflowName": "deploy reports",
                "headSha": REVISION,
                "status": "completed",
                "conclusion": "failure",
                "url": "https://example.test/runs/1",
            },
        ]
        return 0, json.dumps(runs)


def test_a_recorded_failing_verdict_is_requeried_so_a_green_rerun_clears_it(tmp_path):
    configuration = configuration_in(tmp_path)
    record_path = revision_record_path(
        configuration.continuous_integration_directory, REVISION
    )
    write_record(record_path, {"state": "failing", "revision": REVISION})
    runner = RerunPassingForgeRunner()

    status = continuous_integration_for(configuration, runner, REVISION)

    assert status["state"] == "passing"
    assert runner.queries == 1
    assert json.loads(record_path.read_text())["state"] == "passing"


def test_a_recorded_passing_verdict_is_not_requeried(tmp_path):
    configuration = configuration_in(tmp_path)
    record_path = revision_record_path(
        configuration.continuous_integration_directory, REVISION
    )
    write_record(record_path, {"state": "passing", "revision": REVISION})
    runner = RerunPassingForgeRunner()

    status = continuous_integration_for(configuration, runner, REVISION)

    assert status["state"] == "passing"
    assert runner.queries == 0
