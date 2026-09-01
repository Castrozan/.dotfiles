import sys
from pathlib import Path

from ingestion_snapshot_publisher import run_snapshot_publisher

DOTFILES_TEST_BASELINE_TOPIC = "dotfiles-test-baseline"
DOTFILES_TEST_BASELINE_SCHEMA_VERSION = 1
DEFAULT_PRODUCER_LABEL = "dotfiles-agent-evals"
DEFAULT_BASELINE_DOCUMENT_PATH = (
    Path(__file__).resolve().parents[3]
    / "agent-harness"
    / "quality"
    / "evaluations"
    / "baseline.json"
)


def build_execution_role(role_document):
    return {
        "harness": role_document["harness"],
        "model": role_document.get("model"),
        "reasoningEffort": role_document.get("reasoning_effort"),
    }


def build_execution_profile(profile_document):
    return {
        "subject": build_execution_role(profile_document["subject"]),
        "judge": build_execution_role(profile_document["judge"]),
    }


def build_run_source(source_document):
    source = {"kind": source_document["kind"]}
    if "git_commit" in source_document:
        source["gitCommit"] = source_document["git_commit"]
    if "session_id" in source_document:
        source["sessionId"] = source_document["session_id"]
    return source


def build_test_result(test_document):
    return {
        "name": test_document["name"],
        "passed": test_document["passed"],
        "fingerprint": test_document["fingerprint"],
        "generatedAt": test_document["generated_at"],
        "executionProfileId": test_document["execution_profile_id"],
        "runSource": build_run_source(test_document["run_source"]),
    }


def build_provider_usage(usage_document):
    return {
        "invocations": usage_document.get("invocations", 0),
        "measuredInvocations": usage_document.get("measured_invocations", 0),
        "inputTokens": usage_document.get("input_tokens", 0),
        "cachedInputTokens": usage_document.get("cached_input_tokens", 0),
        "cacheWriteInputTokens": usage_document.get("cache_write_input_tokens", 0),
        "outputTokens": usage_document.get("output_tokens", 0),
        "reasoningOutputTokens": usage_document.get("reasoning_output_tokens", 0),
    }


def build_token_usage(token_usage_document):
    return {
        role: {
            harness: build_provider_usage(harnesses[harness])
            for harness in sorted(harnesses)
        }
        for role, harnesses in sorted(token_usage_document.items())
    }


def build_category_result(category_name, category_document):
    return {
        "category": category_name,
        "passed": category_document["passed"],
        "failed": category_document["failed"],
        "tests": [build_test_result(test) for test in category_document["tests"]],
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
        "oldestEvidenceAt": baseline_document["oldest_evidence_at"],
        "minimumCurrentEvidence": baseline_document["minimum_current_evidence"],
        "executionProfile": build_execution_profile(
            baseline_document["execution_profile"]
        ),
        "executionProfiles": [
            {
                "id": profile_identifier,
                **build_execution_profile(
                    baseline_document["execution_profiles"][profile_identifier]
                ),
            }
            for profile_identifier in sorted(baseline_document["execution_profiles"])
        ],
        "tokenUsage": build_token_usage(baseline_document.get("token_usage", {})),
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
