# shellcheck shell=bash

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
