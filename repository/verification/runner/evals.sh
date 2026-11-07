#!/usr/bin/env bash

readonly TIER_SKIPPED_STATUS=77

_run_agent_evals() {
	local tier_title=$1
	shift

	if ! command -v dotfiles-evals &>/dev/null; then
		echo "SKIP: dotfiles-evals not installed, skipping $tier_title" >&2
		return $TIER_SKIPPED_STATUS
	fi

	echo "--- $tier_title ---"
	(cd "$REPO_DIR" && dotfiles-evals run "$@")
	echo ""
}

_run_evals_tier() {
	_run_agent_evals "Agent Evals (LLM)"
}

_run_integration_tier() {
	_run_agent_evals "Integration Workflow Evals (real agent sessions)" --categoria integration_workflows
}

_run_e2e_tier() {
	_run_agent_evals "End-to-end Workflow Evals (real agent sessions)" --categoria end_to_end_workflows
}
