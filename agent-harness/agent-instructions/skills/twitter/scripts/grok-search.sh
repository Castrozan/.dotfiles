#!/usr/bin/env bash
set -Eeuo pipefail

# shellcheck source=grok-search-request.sh
source "$(dirname "${BASH_SOURCE[0]}")/grok-search-request.sh"

readonly XAI_API_ENDPOINT="https://api.x.ai/v1/responses"
readonly XAI_DEFAULT_MODEL="grok-4-latest"
readonly XAI_DEFAULT_TIMEOUT_SECONDS=90
readonly XAI_AUTH_PROFILES_PATH="${XAI_AUTH_PROFILES:-$HOME/.config/xai/auth-profiles.json}"

_print_usage() {
	cat >&2 <<'EOF'
Usage: grok-search [OPTIONS] <query>

Search X/Twitter and the web using xAI's Grok Responses API.

Options:
  --model <model>           Model (default: grok-4-latest)
  --x-only                  X/Twitter posts only
  --web-only                Web results only
  --allowed-domains <d1,d2> Restrict to domains (max 5, comma-separated)
  --excluded-domains <d1,d2> Exclude domains (max 5, comma-separated)
  --timeout <seconds>       Request timeout (default: 90)
  --raw                     Full JSON response
  --cost                    Show token usage and cost on stderr
  --quiet                   Suppress progress on stderr
  --help                    Show this help

Examples:
  grok-search "NixOS trends on Twitter"
  grok-search --x-only --cost "Claude Sonnet 4.6"
  grok-search --web-only --allowed-domains "github.com" "Claude Code"
  grok-search --raw "AI agents" | jq '.output'
EOF
}

_resolve_api_key() {
	if [[ -n "${XAI_API_KEY:-}" ]]; then
		echo "$XAI_API_KEY"
		return
	fi

	if [[ -f "$XAI_AUTH_PROFILES_PATH" ]]; then
		local extracted_key
		extracted_key=$(jq -r '.profiles["xai:manual"].token // empty' "$XAI_AUTH_PROFILES_PATH" 2>/dev/null || true)
		if [[ -n "$extracted_key" ]]; then
			echo "$extracted_key"
			return
		fi
	fi

	echo "Error: No xAI API key found. Set XAI_API_KEY or configure auth-profiles." >&2
	exit 1
}

main() {
	local model="$XAI_DEFAULT_MODEL"
	local timeout_seconds="$XAI_DEFAULT_TIMEOUT_SECONDS"
	local x_only="false"
	local web_only="false"
	local allowed_domains=""
	local excluded_domains=""
	local raw_output="false"
	local show_cost="false"
	local quiet="false"
	local query=""

	while [[ $# -gt 0 ]]; do
		case "$1" in
		--model)
			model="$2"
			shift 2
			;;
		--timeout)
			timeout_seconds="$2"
			shift 2
			;;
		--x-only)
			x_only="true"
			shift
			;;
		--web-only)
			web_only="true"
			shift
			;;
		--allowed-domains)
			allowed_domains="$2"
			shift 2
			;;
		--excluded-domains)
			excluded_domains="$2"
			shift 2
			;;
		--raw)
			raw_output="true"
			shift
			;;
		--cost)
			show_cost="true"
			shift
			;;
		--quiet | -q)
			quiet="true"
			shift
			;;
		--help | -h)
			_print_usage
			exit 0
			;;
		-*)
			echo "Unknown option: $1" >&2
			_print_usage
			exit 1
			;;
		*)
			query="$1"
			shift
			;;
		esac
	done

	if [[ -z "$query" ]]; then
		echo "Error: query is required" >&2
		_print_usage
		exit 1
	fi

	local api_key
	api_key=$(_resolve_api_key)

	local tool_json
	tool_json=$(_build_search_tool_json "$allowed_domains" "$excluded_domains")

	local system_prompt
	system_prompt=$(_build_system_prompt "$x_only" "$web_only")

	local request_body
	request_body=$(_build_request_body "$query" "$model" "$tool_json" "$system_prompt")

	if [[ "$quiet" != "true" ]]; then
		local search_type="web+X"
		[[ "$x_only" == "true" ]] && search_type="X only"
		[[ "$web_only" == "true" ]] && search_type="web only"
		echo "Searching ($search_type)..." >&2
	fi

	local http_code response_file
	response_file=$(mktemp)
	trap "rm -f '$response_file'" EXIT

	http_code=$(curl -s -w '%{http_code}' -o "$response_file" \
		--max-time "$timeout_seconds" \
		"$XAI_API_ENDPOINT" \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer $api_key" \
		-d "$request_body") || {
		local curl_exit=$?
		if [[ $curl_exit -eq 28 ]]; then
			echo "Error: Request timed out after ${timeout_seconds}s. Try --timeout <seconds> to increase." >&2
		else
			echo "Error: curl failed (exit $curl_exit)" >&2
		fi
		exit 1
	}

	local response
	response=$(cat "$response_file")

	_handle_api_error "$response" "$http_code"

	if [[ "$show_cost" == "true" ]]; then
		_print_cost_summary "$response"
	fi

	if [[ "$raw_output" == "true" ]]; then
		echo "$response" | jq '.'
	else
		local extracted_text
		extracted_text=$(echo "$response" | _extract_response_text)
		if [[ -z "$extracted_text" ]]; then
			echo "Warning: No text content in response. Use --raw to inspect." >&2
			exit 1
		fi
		echo "$extracted_text"
	fi
}

main "$@"
