import sys
from pathlib import Path

from ingestion_snapshot_publisher import run_snapshot_publisher

DOTFILES_TEST_QUALITY_TOPIC = "dotfiles-test-quality"
DOTFILES_TEST_QUALITY_SCHEMA_VERSION = 1
DEFAULT_PRODUCER_LABEL = "dotfiles-test-quality-renderer"
DEFAULT_QUALITY_DOCUMENT_PATH = (
    Path(__file__).resolve().parents[1]
    / "apps"
    / "reports"
    / "site"
    / "quality"
    / "metrics.json"
)


def build_static_eval_summary(static_eval_document):
    return {
        "totalTests": static_eval_document["totalTests"],
        "passedTests": static_eval_document["passedTests"],
        "passRate": static_eval_document["passRate"],
        "suiteCount": static_eval_document["suiteCount"],
        "categoryCount": static_eval_document["categoryCount"],
        "recordedAt": static_eval_document["recordedAt"],
        "recordedCommit": static_eval_document["recordedCommit"],
    }


def build_core_rule_summary(core_rule_document):
    return {
        "lineCount": core_rule_document["lineCount"],
        "ruleBlockCount": core_rule_document["ruleBlockCount"],
    }


def build_hook_summary(hook_document):
    return {
        "wiredEvents": list(hook_document["wiredEvents"]),
        "entryPointCount": hook_document["entryPointCount"],
    }


def build_test_quality_payload(quality_metrics_document, environment):
    return {
        "recordedAt": quality_metrics_document["generatedAt"],
        "commit": quality_metrics_document["generatedCommit"],
        "staticEvals": build_static_eval_summary(
            quality_metrics_document["staticEvals"]
        ),
        "integrationScenarioCount": quality_metrics_document[
            "integrationScenarioCount"
        ],
        "endToEndScenarioCount": quality_metrics_document["endToEndScenarioCount"],
        "coreRules": build_core_rule_summary(quality_metrics_document["coreRules"]),
        "hooks": build_hook_summary(quality_metrics_document["hooks"]),
    }


def main(command_line_arguments):
    return run_snapshot_publisher(
        DOTFILES_TEST_QUALITY_TOPIC,
        DOTFILES_TEST_QUALITY_SCHEMA_VERSION,
        DEFAULT_PRODUCER_LABEL,
        build_test_quality_payload,
        command_line_arguments[0]
        if command_line_arguments
        else DEFAULT_QUALITY_DOCUMENT_PATH,
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
