#!/usr/bin/env bash

set -Eeuo pipefail

readonly OPENCLAW_STATE_DIR="${HOME}/.openclaw"
readonly AGENTS_DIR="${OPENCLAW_STATE_DIR}/agents"

main() {
  local agent_name=""
  local session_id=""
  local message_limit=50
  local list_sessions=false
  local show_tools=false

  _parse_arguments "$@"

  if [ -z "$agent_name" ]; then
    _print_usage
    exit 1
  fi

  local sessions_dir="${AGENTS_DIR}/${agent_name}/sessions"

  _ensure_agent_sessions_dir_exists "$sessions_dir" "$agent_name"

  if [ "$list_sessions" = true ]; then
    _list_agent_sessions "$sessions_dir"
    return
  fi

  if [ -z "$session_id" ]; then
    session_id="$(_resolve_latest_session_id "$sessions_dir")"
  fi

  local session_file="${sessions_dir}/${session_id}.jsonl"
  _ensure_session_file_exists "$session_file" "$session_id"
  _render_chat_messages "$session_file" "$message_limit" "$show_tools"
}

_parse_arguments() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --agent | -a)
        agent_name="$2"
        shift 2
        ;;
      --session | -s)
        session_id="$2"
        shift 2
        ;;
      --limit | -n)
        message_limit="$2"
        shift 2
        ;;
      --list | -l)
        list_sessions=true
        shift
        ;;
      --tools | -t)
        show_tools=true
        shift
        ;;
      --help | -h)
        _print_usage
        exit 0
        ;;
      *)
        if [ -z "$agent_name" ]; then
          agent_name="$1"
        fi
        shift
        ;;
    esac
  done
}

_print_usage() {
  cat >&2 <<'USAGE'
Usage: read-agent-chat.sh [OPTIONS] [AGENT_NAME]

Read OpenClaw agent chat history from session JSONL files.

Arguments:
  AGENT_NAME              Agent name (e.g. silver, jenny, robson)

Options:
  -a, --agent NAME        Agent name (alternative to positional)
  -s, --session ID        Session UUID (default: latest)
  -n, --limit N           Number of recent messages to show (default: 50)
  -l, --list              List available sessions instead of reading chat
  -t, --tools             Include tool call/result messages (default: off)
  -h, --help              Show this help

Examples:
  read-agent-chat.sh silver
  read-agent-chat.sh --agent silver --limit 20
  read-agent-chat.sh silver --list
  read-agent-chat.sh silver --session bdf89bf8-5738-47c4-874a-d1389c64f603
  read-agent-chat.sh silver --tools
USAGE
}

_ensure_agent_sessions_dir_exists() {
  local sessions_dir=$1
  local agent_name=$2

  if [ ! -d "$sessions_dir" ]; then
    echo "Error: no sessions directory for agent '${agent_name}' at ${sessions_dir}" >&2
    echo "Available agents:" >&2
    ls "${AGENTS_DIR}" 2>/dev/null | sed 's/^/  /' >&2
    exit 1
  fi
}

_list_agent_sessions() {
  local sessions_dir=$1
  local sessions_json="${sessions_dir}/sessions.json"

  if [ ! -f "$sessions_json" ]; then
    echo "No sessions found." >&2
    return
  fi

  jq -r '
    to_entries
    | map(select(.value.sessionId))
    | sort_by(-.value.updatedAt)
    | .[]
    | "\(.value.sessionId)  \(.value.updatedAt / 1000 | strftime("%Y-%m-%d %H:%M UTC"))  \(.key)"
  ' "$sessions_json"
}

_resolve_latest_session_id() {
  local sessions_dir=$1
  local sessions_json="${sessions_dir}/sessions.json"

  if [ ! -f "$sessions_json" ]; then
    echo "Error: no sessions.json found in ${sessions_dir}" >&2
    exit 1
  fi

  local latest_session_id
  latest_session_id=$(jq -r '
    to_entries
    | map(select(.value.sessionId))
    | sort_by(-.value.updatedAt)
    | .[0].value.sessionId // empty
  ' "$sessions_json")

  if [ -z "$latest_session_id" ]; then
    echo "Error: no sessions found for this agent" >&2
    exit 1
  fi

  echo "$latest_session_id"
}

_ensure_session_file_exists() {
  local session_file=$1
  local session_id=$2

  if [ ! -f "$session_file" ]; then
    echo "Error: session file not found: ${session_file}" >&2
    exit 1
  fi
}

_render_chat_messages() {
  local session_file=$1
  local message_limit=$2
  local show_tools=$3

  local jq_filter

  if [ "$show_tools" = true ]; then
    jq_filter='select(.type == "message")'
  else
    jq_filter='select(.type == "message" and (.message.role == "user" or .message.role == "assistant"))'
  fi

  jq -r "$jq_filter"' |
    .timestamp as $ts |
    .message |
    (
      if .role == "user" then "USER"
      elif .role == "assistant" then "ASSISTANT"
      elif .role == "toolResult" then "TOOL_RESULT"
      else (.role | ascii_upcase)
      end
    ) as $role |
    (
      if (.content | type) == "array" then
        [.content[] | select(.type == "text") | .text] | join("\n")
      elif (.content | type) == "string" then
        .content
      else
        ""
      end
    ) as $text |
    if ($text | length) > 0 then
      "[\($ts)] \($role):\n\($text)\n"
    else
      empty
    end
  ' "$session_file" | tail -n "$((message_limit * 10))"
}

main "$@"
