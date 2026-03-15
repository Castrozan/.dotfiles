#!/usr/bin/env bats

readonly CHROME_USER_DATA_DIR="$HOME/.config/google-chrome"
readonly DEVTOOLS_PORT_FILE="$CHROME_USER_DATA_DIR/DevToolsActivePort"
readonly MCP_BINARY="$HOME/.local/share/chrome-devtools-mcp-npm/bin/chrome-devtools-mcp"
readonly CHROME_LOCAL_STATE="$CHROME_USER_DATA_DIR/Local State"
readonly CHROME_POLICY_FILE="$CHROME_USER_DATA_DIR/policies/managed/agent-browser-control.json"

@test "DevToolsActivePort file exists when Chrome is running" {
  [[ -f "$DEVTOOLS_PORT_FILE" ]]
}

@test "DevToolsActivePort has port on first line" {
  port=$(head -1 "$DEVTOOLS_PORT_FILE")
  [[ "$port" =~ ^[0-9]+$ ]]
}

@test "DevToolsActivePort has WebSocket path on second line" {
  ws_path=$(tail -1 "$DEVTOOLS_PORT_FILE")
  [[ "$ws_path" == /devtools/browser/* ]]
}

@test "chrome-devtools-mcp binary exists and is executable" {
  [[ -x "$MCP_BINARY" ]]
}

@test "Chrome remote debugging toggle is enabled in Local State" {
  value=$(jq -r '.devtools.remote_debugging["user-enabled"]' "$CHROME_LOCAL_STATE")
  [[ "$value" == "true" ]]
}

@test "Chrome enterprise policy file deployed" {
  [[ -f "$CHROME_POLICY_FILE" ]]
  value=$(jq -r '.RemoteDebuggingAllowed' "$CHROME_POLICY_FILE")
  [[ "$value" == "true" ]]
}

@test "MCP server connects and initializes via wsEndpoint" {
  port=$(head -1 "$DEVTOOLS_PORT_FILE")
  ws_path=$(tail -1 "$DEVTOOLS_PORT_FILE")
  ws_url="ws://127.0.0.1:${port}${ws_path}"

  result=$(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}' \
    | timeout 10 "$MCP_BINARY" --wsEndpoint "$ws_url" --usageStatistics false 2>/dev/null \
    | head -1)

  echo "$result" | jq -e '.result.serverInfo.name == "chrome_devtools"'
}

@test "MCP server can list pages" {
  port=$(head -1 "$DEVTOOLS_PORT_FILE")
  ws_path=$(tail -1 "$DEVTOOLS_PORT_FILE")
  ws_url="ws://127.0.0.1:${port}${ws_path}"

  result=$( (echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}'; sleep 3; echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'; sleep 1; echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_pages","arguments":{}}}'; sleep 3) \
    | timeout 15 "$MCP_BINARY" --wsEndpoint "$ws_url" --usageStatistics false 2>/dev/null \
    | tail -1)

  echo "$result" | jq -e '.result.content[0].text' | grep -q "Pages"
}
