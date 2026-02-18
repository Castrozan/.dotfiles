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
    if ! curl -so /dev/null --max-time 2 "$GATEWAY_URL/" 2>/dev/null; then
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
    httpCode=$(curl -so /dev/null -w '%{http_code}' --max-time "$CURL_TIMEOUT" "$GATEWAY_URL/")
    [ "$httpCode" = "200" ]
}

@test "gateway: serves web UI" {
    skip_if_no_gateway
    result=$(curl -s --max-time "$CURL_TIMEOUT" "$GATEWAY_URL/")
    [[ "$result" == *"OpenClaw"* ]]
}

@test "gateway: chat completions endpoint responds" {
    skip_if_no_gateway
    skip_if_no_token
    result=$(gateway_post "/v1/chat/completions" '{
        "model": "anthropic/claude-opus-4-6",
        "messages": [{"role":"user","content":"Reply with ONLY the word ONLINE"}],
        "max_tokens": 5
    }')
    echo "$result" | jq -e '.choices[0].message.content' > /dev/null
}

@test "gateway: chat completions rejects without auth" {
    skip_if_no_gateway
    httpCode=$(curl -so /dev/null -w '%{http_code}' --max-time "$CURL_TIMEOUT" \
        -H "Content-Type: application/json" \
        -d '{"model":"test","messages":[{"role":"user","content":"test"}]}' \
        "$GATEWAY_URL/v1/chat/completions")
    [ "$httpCode" = "401" ] || [ "$httpCode" = "403" ]
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

# ---------- Hindsight memory plugin ----------

skip_if_no_hindsight_daemon() {
    if ! curl -so /dev/null --max-time 2 "http://127.0.0.1:9077/health" 2>/dev/null; then
        skip "hindsight daemon not running on port 9077"
    fi
}

@test "plugins: hindsight-openclaw is memory slot" {
    result=$(jq -r '.plugins.slots.memory' "$HOME/.openclaw/openclaw.json")
    [ "$result" = "hindsight-openclaw" ]
}

@test "plugins: memory-core is disabled" {
    result=$(jq -r '.plugins.entries["memory-core"].enabled' "$HOME/.openclaw/openclaw.json")
    [ "$result" = "false" ]
}

@test "plugins: hindsight daemon is healthy" {
    skip_if_no_hindsight_daemon
    result=$(curl -sf --max-time 5 "http://127.0.0.1:9077/health")
    echo "$result" | jq -e '.status == "healthy"' > /dev/null
}

@test "plugins: hindsight binary is functional" {
    [ -f "$HOME/.local/bin/hindsight" ]
    run "$HOME/.local/bin/hindsight" --version
    [ "$status" -eq 0 ]
    [[ "$output" == hindsight* ]]
}

@test "plugins: pgvector is glibc compatible" {
    vectorSo=$(find "$HOME/.pg0/installation" -name "vector.so" 2>/dev/null | head -1)
    if [ -z "$vectorSo" ]; then
        skip "no pg0 vector.so found"
    fi
    run bash -c "strings '$vectorSo' | grep -E 'GLIBC_2\.(3[89]|[4-9][0-9])'"
    [ "$status" -ne 0 ]
}

@test "plugins: hindsight client.js uses HTTP retain" {
    clientJs="$HOME/.openclaw/extensions/hindsight-openclaw/dist/client.js"
    if [ ! -f "$clientJs" ]; then
        skip "hindsight extension not installed"
    fi
    grep -q "HINDSIGHT_DAEMON_BASE_URL" "$clientJs"
}

# ---------- QMD memory backend ----------

@test "memory: qmd backend is configured" {
    result=$(jq -r '.memory.backend' "$HOME/.openclaw/openclaw.json")
    [ "$result" = "qmd" ]
}

@test "memory: qmd data directory exists for agents" {
    qmdDirCount=$(find "$HOME/.openclaw/agents" -maxdepth 2 -type d -name "qmd" 2>/dev/null | wc -l)
    [ "$qmdDirCount" -gt 0 ]
}
