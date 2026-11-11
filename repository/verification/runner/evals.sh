#!/usr/bin/env bash

readonly TIER_SKIPPED_STATUS=77
readonly TIER_EVALUATION_REPORTS_DIRECTORY="${XDG_STATE_HOME:-$HOME/.local/state}/dotfiles-test-tier-evaluations"

_run_agent_evals() {
	local tier_title=$1
	local tier_name=$2
	shift 2

	if ! command -v dotfiles-evals &>/dev/null; then
		echo "SKIP: dotfiles-evals not installed, skipping $tier_title" >&2
		return $TIER_SKIPPED_STATUS
	fi

	local tier_report_path="$TIER_EVALUATION_REPORTS_DIRECTORY/$tier_name/relatorio.html"
	local evaluation_status=0
	echo "--- $tier_title ---"
	echo "report: $tier_report_path"
	(cd "$REPO_DIR" && dotfiles-evals run --relatorio "$tier_report_path" "$@") || evaluation_status=$?
	echo ""
	return "$evaluation_status"
}

_run_evals_tier() {
	_run_agent_evals "Agent Evals (LLM)" evals
}

_run_integration_tier() {
	_run_agent_evals "Integration Workflow Evals (real agent sessions)" integration --categoria integration_workflows
}

_run_e2e_tier() {
	_run_agent_evals "End-to-end Workflow Evals (real agent sessions)" e2e --categoria end_to_end_workflows
}
