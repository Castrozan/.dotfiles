#!/usr/bin/env bash

_run_evals_tier() {
	if ! command -v claude &>/dev/null; then
		echo "SKIP: claude CLI not installed, skipping agent evals" >&2
		return 0
	fi

	echo "--- Agent Evals (LLM) ---"
	"$REPO_DIR/agents/evals/run-evals.py"
	echo ""
}

_run_integration_tier() {
	if ! command -v claude &>/dev/null; then
		echo "SKIP: claude CLI not installed, skipping integration tests" >&2
		return 0
	fi

	echo "--- Integration Tests (real Claude sessions) ---"
	"$REPO_DIR/agents/evals/integration/run-integration-tests.py"
	echo ""
}

_run_e2e_tier() {
	if ! command -v claude &>/dev/null; then
		echo "SKIP: claude CLI not installed, skipping E2E tests" >&2
		return 0
	fi
	if ! command -v tmux &>/dev/null; then
		echo "SKIP: tmux not installed, skipping E2E tests" >&2
		return 0
	fi

	echo "--- E2E Tests (tmux interactive Claude sessions) ---"
	"$REPO_DIR/agents/evals/e2e/run-e2e-tests.py"
	echo ""
}
