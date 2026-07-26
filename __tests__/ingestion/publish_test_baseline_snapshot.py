import sys
from pathlib import Path

from ingestion_snapshot_publisher import run_snapshot_publisher

DOTFILES_TEST_BASELINE_TOPIC = "dotfiles-test-baseline"
DOTFILES_TEST_BASELINE_SCHEMA_VERSION = 1
DEFAULT_PRODUCER_LABEL = "dotfiles-agent-evals"
DEFAULT_BASELINE_DOCUMENT_PATH = (
    Path(__file__).resolve().parents[2] / "agents" / "__tests__" / "baseline.json"
)


def build_category_result(category_name, category_document):
    return {
        "category": category_name,
        "passed": category_document["passed"],
        "failed": category_document["failed"],
        "tests": [
            {"name": test["name"], "passed": test["passed"]}
            for test in category_document["tests"]
        ],
    }


def build_test_baseline_payload(baseline_document, environment=None):
    categories = baseline_document["categories"]
    return {
        "recordedAt": baseline_document["generated_at"],
        "commit": baseline_document["git_commit"],
        "totalTests": baseline_document["total_tests"],
        "passedTests": baseline_document["total_passed"],
        "failedTests": baseline_document["total_failed"],
        "passRate": baseline_document["pass_rate"],
        "categories": [
            build_category_result(category_name, categories[category_name])
            for category_name in sorted(categories)
        ],
    }


def main(command_line_arguments):
    return run_snapshot_publisher(
        DOTFILES_TEST_BASELINE_TOPIC,
        DOTFILES_TEST_BASELINE_SCHEMA_VERSION,
        DEFAULT_PRODUCER_LABEL,
        build_test_baseline_payload,
        command_line_arguments[0]
        if command_line_arguments
        else DEFAULT_BASELINE_DOCUMENT_PATH,
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
