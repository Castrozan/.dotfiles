#!/usr/bin/env bash

_run_evals_tier() {
	if ! command -v agent-eval &>/dev/null; then
		echo "SKIP: agent-eval not installed, skipping agent evals" >&2
		return 0
	fi

	echo "--- Agent Evals (LLM) ---"
	# Through the packaged command, never the raw script: agent-eval puts the unwrapped claude ahead of the
	# interactive wrapper, and a wrapped subject scores the live machine instead of the declared instruction paths.
	agent-eval
	echo ""
}

_run_integration_tier() {
	if ! command -v claude &>/dev/null; then
		echo "SKIP: claude CLI not installed, skipping integration tests" >&2
		return 0
	fi

	echo "--- Integration Tests (real Claude sessions) ---"
	"$REPO_DIR/agent-harness/quality/evaluations/integration/run-integration-tests.py"
	echo ""
}

_run_e2e_tier() {
	if ! command -v claude &>/dev/null; then
		echo "SKIP: claude CLI not installed, skipping E2E tests" >&2
		return 0
	fi
	if ! command -v herdr &>/dev/null; then
		echo "SKIP: herdr not installed, skipping E2E tests" >&2
		return 0
	fi

	echo "--- E2E Tests (herdr interactive Claude sessions) ---"
	"$REPO_DIR/agent-harness/quality/evaluations/e2e/run-e2e-tests.py"
	echo ""
}
