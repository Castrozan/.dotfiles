#!/usr/bin/env bats

setup() {
    GATEWAY_PORT=${OPENCLAW_GATEWAY_PORT:-18790}
    GATEWAY_URL="http://localhost:$GATEWAY_PORT"
    GATEWAY_TOKEN_FILE="$HOME/.openclaw/secrets/openclaw-gateway-token"

    if [ -f "$GATEWAY_TOKEN_FILE" ]; then
        GATEWAY_TOKEN=$(cat "$GATEWAY_TOKEN_FILE" | tr -d '\n')
    else
        GATEWAY_TOKEN="${OPENCLAW_GATEWAY_TOKEN:-}"
    fi

    CURL_TIMEOUT=10
}

skip_if_no_gateway() {
    if ! curl -sf --max-time 2 "$GATEWAY_URL/health" > /dev/null 2>&1; then
        skip "gateway not running on $GATEWAY_URL"
    fi
}

skip_if_no_token() {
    if [ -z "$GATEWAY_TOKEN" ]; then
        skip "no gateway token available"
    fi
}

gateway_get() {
    local path="$1"
    curl -sf --max-time "$CURL_TIMEOUT" \
        -H "Authorization: Bearer $GATEWAY_TOKEN" \
        "$GATEWAY_URL$path"
}

gateway_post() {
    local path="$1"
    local body="$2"
    curl -sf --max-time "$CURL_TIMEOUT" \
        -H "Authorization: Bearer $GATEWAY_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$body" \
        "$GATEWAY_URL$path"
}

# ---------- Gateway health ----------

@test "gateway: responds on expected port" {
    skip_if_no_gateway
    run curl -sf --max-time "$CURL_TIMEOUT" "$GATEWAY_URL/health"
    [ "$status" -eq 0 ]
}

@test "gateway: health endpoint returns valid JSON" {
    skip_if_no_gateway
    result=$(curl -sf --max-time "$CURL_TIMEOUT" "$GATEWAY_URL/health")
    echo "$result" | jq -e . > /dev/null
}

@test "gateway: authenticated request succeeds" {
    skip_if_no_gateway
    skip_if_no_token
    run gateway_get "/api/agents"
    [ "$status" -eq 0 ]
}

@test "gateway: unauthenticated request to protected endpoint fails" {
    skip_if_no_gateway
    run curl -sf --max-time "$CURL_TIMEOUT" "$GATEWAY_URL/api/agents"
    [ "$status" -ne 0 ]
}

# ---------- Agent availability ----------

@test "gateway: agents list is not empty" {
    skip_if_no_gateway
    skip_if_no_token
    result=$(gateway_get "/api/agents")
    count=$(echo "$result" | jq 'length')
    [ "$count" -gt 0 ]
}

@test "gateway: expected agents are registered" {
    skip_if_no_gateway
    skip_if_no_token
    result=$(gateway_get "/api/agents")
    agentIds=$(echo "$result" | jq -r '.[].id')
    for expected in robson jarvis; do
        echo "$agentIds" | grep -q "$expected"
    done
}

@test "gateway: agent responds to prompt" {
    skip_if_no_gateway
    skip_if_no_token
    result=$(gateway_post "/v1/chat/completions" '{
        "model": "anthropic/claude-opus-4-6",
        "messages": [{"role":"user","content":"Reply with only the word ONLINE"}],
        "max_tokens": 10,
        "agentId": "jarvis"
    }')
    echo "$result" | jq -e '.choices[0].message.content' > /dev/null
}

# ---------- Systemd services ----------

@test "systemd: openclaw-gateway service is active" {
    run systemctl --user is-active openclaw-gateway.service
    [ "$output" = "active" ]
}

@test "systemd: openclaw-gateway service is enabled" {
    run systemctl --user is-enabled openclaw-gateway.service
    [ "$output" = "enabled" ]
}

@test "systemd: memory sync timer is active" {
    run systemctl --user is-active openclaw-memory-sync.timer
    [ "$output" = "active" ]
}

@test "systemd: memory sync timer is enabled" {
    run systemctl --user is-enabled openclaw-memory-sync.timer
    [ "$output" = "enabled" ]
}

@test "systemd: gateway service has OPENCLAW_NIX_MODE set" {
    result=$(systemctl --user show openclaw-gateway.service -p Environment 2>/dev/null || true)
    [[ "$result" == *"OPENCLAW_NIX_MODE=1"* ]]
}

@test "systemd: gateway service has NODE_ENV=production" {
    result=$(systemctl --user show openclaw-gateway.service -p Environment 2>/dev/null || true)
    [[ "$result" == *"NODE_ENV=production"* ]]
}

# ---------- Directory structure ----------

@test "directories: agent workspaces exist" {
    for agent_workspace in openclaw/robson openclaw/jarvis; do
        [ -d "$HOME/$agent_workspace" ]
    done
}

@test "directories: memory dirs exist for synced agents" {
    [ -d "$HOME/openclaw/jarvis/memory" ]
}

@test "directories: projects dirs exist" {
    for agent_workspace in openclaw/robson openclaw/jarvis; do
        [ -d "$HOME/$agent_workspace/projects" ]
    done
}

@test "directories: seed files exist" {
    for agent_workspace in openclaw/robson openclaw/jarvis; do
        [ -f "$HOME/$agent_workspace/HEARTBEAT.md" ]
        [ -f "$HOME/$agent_workspace/TOOLS.md" ]
    done
}

# ---------- Config file ----------

@test "config: openclaw.json exists" {
    [ -f "$HOME/.openclaw/openclaw.json" ]
}

@test "config: openclaw.json is valid JSON" {
    jq -e . "$HOME/.openclaw/openclaw.json" > /dev/null
}

@test "config: gateway port matches expected" {
    result=$(jq '.gateway.port' "$HOME/.openclaw/openclaw.json")
    [ "$result" = "$GATEWAY_PORT" ]
}

@test "config: agents list includes jarvis" {
    jq -e '.agents.list[] | select(.id == "jarvis")' "$HOME/.openclaw/openclaw.json" > /dev/null
}

@test "config: jarvis workspace path is absolute" {
    result=$(jq -r '.agents.list[] | select(.id == "jarvis") | .workspace' "$HOME/.openclaw/openclaw.json")
    [[ "$result" == /* ]]
}

@test "config: overlay JSON exists" {
    [ -f "$HOME/.openclaw/nix-overlay.json" ]
}

@test "config: overlay JSON is valid" {
    jq -e . "$HOME/.openclaw/nix-overlay.json" > /dev/null
}

# ---------- Workspace deployment ----------

@test "deploy: tts.json exists in workspaces" {
    for agent_workspace in openclaw/robson openclaw/jarvis; do
        [ -f "$HOME/$agent_workspace/tts.json" ]
    done
}

@test "deploy: tts.json is valid JSON" {
    jq -e . "$HOME/openclaw/jarvis/tts.json" > /dev/null
}

@test "deploy: jarvis tts.json has correct voice" {
    result=$(jq -r '.voice' "$HOME/openclaw/jarvis/tts.json")
    [ "$result" = "en-GB-RyanNeural" ]
}

@test "deploy: AGENTS.md exists in workspaces" {
    for agent_workspace in openclaw/robson openclaw/jarvis; do
        [ -f "$HOME/$agent_workspace/AGENTS.md" ]
    done
}

@test "deploy: skills directory exists" {
    for agent_workspace in openclaw/robson openclaw/jarvis; do
        [ -d "$HOME/$agent_workspace/skills" ]
    done
}
