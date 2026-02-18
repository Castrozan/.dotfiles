#!/usr/bin/env bash
set -Eeuo pipefail

readonly XAI_API_ENDPOINT="https://api.x.ai/v1/responses"
readonly XAI_DEFAULT_MODEL="grok-4-latest"
readonly XAI_DEFAULT_TIMEOUT_SECONDS=90
readonly XAI_AUTH_PROFILES_PATH="$HOME/.openclaw/agents/robson/agent/auth-profiles.json"

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
  grok-search --web-only --allowed-domains "github.com" "OpenClaw"
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

_build_search_tool_json() {
  local allowed_domains="${1:-}"
  local excluded_domains="${2:-}"

  local tool_json='{"type": "web_search"}'

  if [[ -n "$allowed_domains" ]]; then
    local domains_array
    domains_array=$(echo "$allowed_domains" | jq -R 'split(",")')
    tool_json=$(echo "$tool_json" | jq --argjson domains "$domains_array" '. + {filters: {allowed_domains: $domains}}')
  elif [[ -n "$excluded_domains" ]]; then
    local domains_array
    domains_array=$(echo "$excluded_domains" | jq -R 'split(",")')
    tool_json=$(echo "$tool_json" | jq --argjson domains "$domains_array" '. + {filters: {excluded_domains: $domains}}')
  fi

  echo "$tool_json"
}

_build_system_prompt() {
  local x_only="${1:-false}"
  local web_only="${2:-false}"

  if [[ "$x_only" == "true" ]]; then
    echo "You are a research assistant. Focus ONLY on X/Twitter posts and discussions. Cite specific tweets with links when possible. Ignore general web results."
  elif [[ "$web_only" == "true" ]]; then
    echo "You are a research assistant. Focus ONLY on web search results. Ignore X/Twitter posts."
  else
    echo "You are a research assistant with access to live web and X/Twitter search. Cite sources with links."
  fi
}

_build_request_body() {
  local query="$1"
  local model="$2"
  local tool_json="$3"
  local system_prompt="$4"

  jq -n \
    --arg model "$model" \
    --arg system_prompt "$system_prompt" \
    --arg query "$query" \
    --argjson tool "$tool_json" \
    '{
      model: $model,
      input: [
        {role: "system", content: $system_prompt},
        {role: "user", content: $query}
      ],
      tools: [$tool]
    }'
}

_extract_response_text() {
  jq -r '
    .output[]
    | select(.type == "message")
    | .content[]
    | select(.type == "output_text")
    | .text
  ' 2>/dev/null
}

_print_cost_summary() {
  local response="$1"
  local usage
  usage=$(echo "$response" | jq '.usage // empty' 2>/dev/null)

  if [[ -z "$usage" || "$usage" == "null" ]]; then
    return
  fi

  local input_tokens output_tokens total_tokens cost_ticks
  input_tokens=$(echo "$usage" | jq -r '.input_tokens // 0')
  output_tokens=$(echo "$usage" | jq -r '.output_tokens // 0')
  total_tokens=$(echo "$usage" | jq -r '.total_tokens // 0')
  cost_ticks=$(echo "$usage" | jq -r '.cost_in_usd_ticks // 0')

  local x_searches web_searches
  x_searches=$(echo "$usage" | jq -r '.server_side_tool_usage_details.x_search_calls // 0')
  web_searches=$(echo "$usage" | jq -r '.server_side_tool_usage_details.web_search_calls // 0')

  local cost_usd
  cost_usd=$(awk "BEGIN { printf \"%.4f\", $cost_ticks / 10000000000 }")

  echo "--- Cost: \$${cost_usd} | Tokens: ${input_tokens}in/${output_tokens}out (${total_tokens} total) | Searches: ${web_searches} web, ${x_searches} X ---" >&2
}

_handle_api_error() {
  local response="$1"
  local http_code="$2"

  if [[ "$http_code" -ne 200 ]]; then
    local error_message
    error_message=$(echo "$response" | jq -r '.error.message // .error // "Unknown error"' 2>/dev/null || echo "HTTP $http_code")
    echo "Error (HTTP $http_code): $error_message" >&2
    exit 1
  fi

  if echo "$response" | jq -e '.error' >/dev/null 2>&1; then
    local error_message
    error_message=$(echo "$response" | jq -r '.error.message // .error' 2>/dev/null)
    echo "API Error: $error_message" >&2
    exit 1
  fi
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
      --model) model="$2"; shift 2 ;;
      --timeout) timeout_seconds="$2"; shift 2 ;;
      --x-only) x_only="true"; shift ;;
      --web-only) web_only="true"; shift ;;
      --allowed-domains) allowed_domains="$2"; shift 2 ;;
      --excluded-domains) excluded_domains="$2"; shift 2 ;;
      --raw) raw_output="true"; shift ;;
      --cost) show_cost="true"; shift ;;
      --quiet|-q) quiet="true"; shift ;;
      --help|-h) _print_usage; exit 0 ;;
      -*) echo "Unknown option: $1" >&2; _print_usage; exit 1 ;;
      *) query="$1"; shift ;;
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
