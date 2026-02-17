#!/usr/bin/env bash
set -Eeuo pipefail

readonly XAI_API_ENDPOINT="https://api.x.ai/v1/responses"
readonly XAI_DEFAULT_MODEL="grok-4-latest"
readonly XAI_AUTH_PROFILES_PATH="$HOME/.openclaw/agents/robson/agent/auth-profiles.json"

_print_usage() {
  cat >&2 <<'EOF'
Usage: grok-search [OPTIONS] <query>

Search X/Twitter and the web using xAI's Grok Responses API with live search.

Options:
  --model <model>           Model to use (default: grok-4-latest)
  --x-only                  Only search X/Twitter (exclude web results)
  --web-only                Only search the web (exclude X/Twitter)
  --allowed-domains <d1,d2> Only search within these domains (max 5, comma-separated)
  --excluded-domains <d1,d2> Exclude these domains (max 5, comma-separated)
  --raw                     Output raw JSON response instead of extracted text
  --help                    Show this help

Environment:
  XAI_API_KEY               API key (falls back to auth-profiles.json)

Examples:
  grok-search "What's trending about NixOS on Twitter?"
  grok-search --x-only "OpenClaw latest updates"
  grok-search --allowed-domains "github.com,x.com" "Claude Code agent"
  grok-search --raw "AI agents news" | jq '.output'
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

  echo "Error: No xAI API key found. Set XAI_API_KEY or configure via openclaw models auth paste-token --provider xai" >&2
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

_build_request_body() {
  local query="$1"
  local model="$2"
  local tool_json="$3"
  local x_only="${4:-false}"
  local web_only="${5:-false}"

  local system_prompt="You are a research assistant with access to live web and X/Twitter search."
  if [[ "$x_only" == "true" ]]; then
    system_prompt="You are a research assistant. Focus ONLY on X/Twitter posts and discussions. Ignore general web results."
  elif [[ "$web_only" == "true" ]]; then
    system_prompt="You are a research assistant. Focus ONLY on web search results. Ignore X/Twitter posts."
  fi

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

main() {
  local model="$XAI_DEFAULT_MODEL"
  local x_only="false"
  local web_only="false"
  local allowed_domains=""
  local excluded_domains=""
  local raw_output="false"
  local query=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --model) model="$2"; shift 2 ;;
      --x-only) x_only="true"; shift ;;
      --web-only) web_only="true"; shift ;;
      --allowed-domains) allowed_domains="$2"; shift 2 ;;
      --excluded-domains) excluded_domains="$2"; shift 2 ;;
      --raw) raw_output="true"; shift ;;
      --help) _print_usage; exit 0 ;;
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

  local request_body
  request_body=$(_build_request_body "$query" "$model" "$tool_json" "$x_only" "$web_only")

  local response
  response=$(curl -s "$XAI_API_ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $api_key" \
    -d "$request_body")

  if echo "$response" | jq -e '.error' >/dev/null 2>&1; then
    echo "API Error: $(echo "$response" | jq -r '.error')" >&2
    exit 1
  fi

  if [[ "$raw_output" == "true" ]]; then
    echo "$response" | jq '.'
  else
    echo "$response" | _extract_response_text
  fi
}

main "$@"
