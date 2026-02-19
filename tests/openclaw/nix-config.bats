#!/usr/bin/env bats

load "../helpers/test-status-tracker.bash"

setup_file() {
    _initialize_test_status_tracking
}

setup() {
    REPO_DIR="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"

    WORKPC_CONFIG='.#homeConfigurations."lucas.zanoni@x86_64-linux".config'
    NIXOS_CONFIG='.#nixosConfigurations.zanoni.config.home-manager.users.zanoni'

    WORKPC_OC="$WORKPC_CONFIG.openclaw"
    NIXOS_OC="$NIXOS_CONFIG.openclaw"
}

teardown() {
    _record_test_failure_if_any
}

teardown_file() {
    _write_passing_status_if_all_passed
}

nix_eval() {
    local expr="$1"
    shift
    nix eval "$expr" "$@" 2>/dev/null
}

nix_eval_json() {
    nix_eval "$1" --json "${@:2}"
}

nix_eval_json_apply() {
    nix_eval "$1" --json --apply "$2" "${@:3}"
}

# ---------- Flake evaluation ----------

@test "flake: homeConfiguration evaluates without errors" {
    run nix_eval_json_apply "$WORKPC_OC.enabledAgents" 'x: builtins.attrNames x'
    [ "$status" -eq 0 ]
}

@test "flake: nixosConfiguration evaluates without errors" {
    run nix_eval_json_apply "$NIXOS_OC.enabledAgents" 'x: builtins.attrNames x'
    [ "$status" -eq 0 ]
}

# ---------- Agent configuration (workpc) ----------

@test "workpc: enabled agents include robson jenny monster silver" {
    result=$(nix_eval_json_apply "$WORKPC_OC.enabledAgents" 'x: builtins.attrNames x')
    for agent in robson jenny monster silver; do
        echo "$result" | jq -e "index(\"$agent\")" > /dev/null
    done
}

@test "workpc: default agent is robson" {
    result=$(nix_eval_json "$WORKPC_OC.defaultAgent")
    [ "$result" = '"robson"' ]
}

@test "workpc: robson is marked as default" {
    result=$(nix_eval_json "$WORKPC_OC.agents.robson.isDefault")
    [ "$result" = "true" ]
}

# ---------- Agent configuration (NixOS) ----------

@test "nixos: enabled agents include clever golden jarvis" {
    result=$(nix_eval_json_apply "$NIXOS_OC.enabledAgents" 'x: builtins.attrNames x')
    for agent in clever golden jarvis; do
        echo "$result" | jq -e "index(\"$agent\")" > /dev/null
    done
}

@test "nixos: default agent is clever" {
    result=$(nix_eval_json "$NIXOS_OC.defaultAgent")
    [ "$result" = '"clever"' ]
}

@test "nixos: jarvis telegram is enabled" {
    result=$(nix_eval_json "$NIXOS_OC.agents.jarvis.telegram.enable")
    [ "$result" = "true" ]
}

@test "nixos: jarvis telegram bot name is Jarvis" {
    result=$(nix_eval_json "$NIXOS_OC.agents.jarvis.telegram.botName")
    [ "$result" = '"Jarvis"' ]
}

@test "nixos: clever is marked as default" {
    result=$(nix_eval_json "$NIXOS_OC.agents.clever.isDefault")
    [ "$result" = "true" ]
}

# ---------- Config patches (workpc) ----------

@test "workpc: gateway port patch is 18790" {
    result=$(nix_eval_json "$WORKPC_OC.configPatches.\".gateway.port\"")
    [ "$result" = "18790" ]
}

@test "workpc: agents list patch has all enabled agents" {
    result=$(nix_eval_json_apply "$WORKPC_OC.configPatches.\".agents.list\"" 'x: map (a: a.id) x')
    for agent in robson jenny monster silver; do
        echo "$result" | jq -e "index(\"$agent\")" > /dev/null
    done
}

@test "workpc: agents list marks robson as default" {
    result=$(nix_eval_json_apply "$WORKPC_OC.configPatches.\".agents.list\"" \
        'x: builtins.filter (a: a ? default && a.default) x')
    echo "$result" | jq -e '.[0].id == "robson"' > /dev/null
}

@test "workpc: agents list has correct workspace paths" {
    result=$(nix_eval_json_apply "$WORKPC_OC.configPatches.\".agents.list\"" \
        'x: builtins.filter (a: a.id == "robson") x')
    echo "$result" | jq -e '.[0].workspace == "/home/lucas.zanoni/openclaw/robson"' > /dev/null
}

@test "workpc: telegram accounts include robson jenny monster silver" {
    result=$(nix_eval_json_apply "$WORKPC_OC.configPatches" 'builtins.attrNames')
    for agent in robson jenny monster silver; do
        echo "$result" | jq -e "index(\".channels.telegram.accounts.$agent\")" > /dev/null
    done
}

@test "workpc: no telegram account for jarvis" {
    result=$(nix_eval_json_apply "$WORKPC_OC.configPatches" 'builtins.attrNames')
    run bash -c "echo '$result' | jq -e 'index(\".channels.telegram.accounts.jarvis\")'"
    [ "$status" -ne 0 ]
}

@test "workpc: bindings exist for telegram-enabled agents" {
    result=$(nix_eval_json_apply "$WORKPC_OC.configPatches.\".bindings\"" \
        'x: map (b: b.agentId) x')
    for agent in robson jenny monster silver; do
        echo "$result" | jq -e "index(\"$agent\")" > /dev/null
    done
}

@test "workpc: no binding for jarvis" {
    result=$(nix_eval_json_apply "$WORKPC_OC.configPatches.\".bindings\"" \
        'x: map (b: b.agentId) x')
    run bash -c "echo '$result' | jq -e 'index(\"jarvis\")'"
    [ "$status" -ne 0 ]
}

@test "workpc: gateway mode is local" {
    result=$(nix_eval_json "$WORKPC_OC.configPatches.\".gateway.mode\"")
    [ "$result" = '"local"' ]
}

@test "workpc: compaction mode is safeguard" {
    result=$(nix_eval_json "$WORKPC_OC.configPatches.\".agents.defaults.compaction.mode\"")
    [ "$result" = '"safeguard"' ]
}

@test "workpc: memory search is enabled" {
    result=$(nix_eval_json "$WORKPC_OC.configPatches.\".agents.defaults.memorySearch.enabled\"")
    [ "$result" = "true" ]
}

# ---------- Config patches (NixOS) ----------

@test "nixos: gateway port patch is 18789" {
    result=$(nix_eval_json "$NIXOS_OC.configPatches.\".gateway.port\"")
    [ "$result" = "18789" ]
}

@test "nixos: telegram accounts include clever golden jarvis" {
    result=$(nix_eval_json_apply "$NIXOS_OC.configPatches" 'builtins.attrNames')
    for agent in clever golden jarvis; do
        echo "$result" | jq -e "index(\".channels.telegram.accounts.$agent\")" > /dev/null
    done
}

@test "nixos: jarvis telegram account name is Jarvis" {
    result=$(nix_eval_json "$NIXOS_OC.configPatches.\".channels.telegram.accounts.jarvis\"")
    echo "$result" | jq -e '.name == "Jarvis"' > /dev/null
}

@test "nixos: clever telegram account uses default capitalized name" {
    result=$(nix_eval_json "$NIXOS_OC.configPatches.\".channels.telegram.accounts.clever\"")
    echo "$result" | jq -e '.name == "Clever"' > /dev/null
}

# ---------- Secret patches ----------

@test "workpc: secret patches include gateway auth token" {
    result=$(nix_eval_json_apply "$WORKPC_OC.secretPatches" 'builtins.attrNames')
    echo "$result" | jq -e 'index(".gateway.auth.token")' > /dev/null
}

@test "workpc: gateway token path is agenix managed" {
    result=$(nix_eval_json "$WORKPC_OC.secretPatches.\".gateway.auth.token\"")
    [[ "$result" == *".secrets/"* ]]
}

@test "workpc: telegram bot token secrets for enabled telegram agents" {
    result=$(nix_eval_json_apply "$WORKPC_OC.secretPatches" 'builtins.attrNames')
    for agent in robson jenny monster silver; do
        echo "$result" | jq -e "index(\".channels.telegram.accounts.$agent.botToken\")" > /dev/null
    done
}

@test "workpc: no telegram bot token secret for jarvis" {
    result=$(nix_eval_json_apply "$WORKPC_OC.secretPatches" 'builtins.attrNames')
    run bash -c "echo '$result' | jq -e 'index(\".channels.telegram.accounts.jarvis.botToken\")'"
    [ "$status" -ne 0 ]
}

@test "nixos: secret patches use /run/agenix/ paths" {
    result=$(nix_eval_json "$NIXOS_OC.secretPatches.\".gateway.auth.token\"")
    [[ "$result" == *"/run/agenix/"* ]]
}

@test "nixos: telegram bot token secret for jarvis exists" {
    result=$(nix_eval_json_apply "$NIXOS_OC.secretPatches" 'builtins.attrNames')
    echo "$result" | jq -e 'index(".channels.telegram.accounts.jarvis.botToken")' > /dev/null
}

# ---------- Default model configuration ----------

@test "workpc: default primary model is opus" {
    result=$(nix_eval_json "$WORKPC_OC.configPatches.\".agents.defaults.model.primary\"")
    [ "$result" = '"anthropic/claude-opus-4-6"' ]
}

@test "workpc: model aliases include opus sonnet codex" {
    result=$(nix_eval_json_apply "$WORKPC_OC.configPatches.\".agents.defaults.models\"" 'builtins.attrNames')
    echo "$result" | jq -e 'index("anthropic/claude-opus-4-6")' > /dev/null
    echo "$result" | jq -e 'index("anthropic/claude-sonnet-4-5")' > /dev/null
    echo "$result" | jq -e 'index("openai-codex/gpt-5.3-codex")' > /dev/null
}

# ---------- Gateway service ----------

@test "workpc: gateway service is defined" {
    result=$(nix_eval_json_apply "$WORKPC_CONFIG.systemd.user.services" 'builtins.attrNames')
    echo "$result" | jq -e 'index("openclaw-gateway")' > /dev/null
}

@test "workpc: gateway service has correct restart policy" {
    result=$(nix_eval_json "$WORKPC_CONFIG.systemd.user.services.openclaw-gateway.Service.Restart")
    [ "$result" = '"always"' ]
}

@test "workpc: gateway service environment has OPENCLAW_NIX_MODE" {
    result=$(nix_eval_json "$WORKPC_CONFIG.systemd.user.services.openclaw-gateway.Service.Environment")
    echo "$result" | jq -e 'map(select(startswith("OPENCLAW_NIX_MODE"))) | length > 0' > /dev/null
}

@test "workpc: gateway service environment has NODE_ENV=production" {
    result=$(nix_eval_json "$WORKPC_CONFIG.systemd.user.services.openclaw-gateway.Service.Environment")
    echo "$result" | jq -e 'index("NODE_ENV=production")' > /dev/null
}

@test "workpc: gateway service PATH includes git" {
    result=$(nix_eval_json "$WORKPC_CONFIG.systemd.user.services.openclaw-gateway.Service.Environment")
    pathEntry=$(echo "$result" | jq -r '.[] | select(startswith("PATH="))')
    [[ "$pathEntry" == *"/bin"* ]]
}

@test "workpc: gateway service wanted by default.target" {
    result=$(nix_eval_json "$WORKPC_CONFIG.systemd.user.services.openclaw-gateway.Install.WantedBy")
    echo "$result" | jq -e 'index("default.target")' > /dev/null
}

# ---------- Memory sync ----------

@test "workpc: memory sync service is defined" {
    result=$(nix_eval_json_apply "$WORKPC_CONFIG.systemd.user.services" 'builtins.attrNames')
    echo "$result" | jq -e 'index("openclaw-memory-sync")' > /dev/null
}

@test "workpc: memory sync timer is defined" {
    result=$(nix_eval_json_apply "$WORKPC_CONFIG.systemd.user.timers" 'builtins.attrNames')
    echo "$result" | jq -e 'index("openclaw-memory-sync")' > /dev/null
}

@test "workpc: memory sync service is oneshot" {
    result=$(nix_eval_json "$WORKPC_CONFIG.systemd.user.services.openclaw-memory-sync.Service.Type")
    [ "$result" = '"oneshot"' ]
}

@test "workpc: memory sync timer wanted by timers.target" {
    result=$(nix_eval_json "$WORKPC_CONFIG.systemd.user.timers.openclaw-memory-sync.Install.WantedBy")
    echo "$result" | jq -e 'index("timers.target")' > /dev/null
}

@test "workpc: memory sync configured for local agents" {
    result=$(nix_eval_json "$WORKPC_OC.memorySync.agents")
    for agent in robson jenny monster silver; do
        echo "$result" | jq -e "index(\"$agent\")" > /dev/null
    done
}

@test "workpc: memory sync remote host is dellg15" {
    result=$(nix_eval_json "$WORKPC_OC.memorySync.remoteHost")
    [ "$result" = '"dellg15"' ]
}

@test "nixos: memory sync remote host is workpc" {
    result=$(nix_eval_json "$NIXOS_OC.memorySync.remoteHost")
    [ "$result" = '"workpc"' ]
}

# ---------- Overlay JSON structure ----------

@test "workpc: nix-overlay.json file is generated" {
    result=$(nix_eval_json_apply "$WORKPC_CONFIG.home.file" \
        'x: builtins.hasAttr ".openclaw/nix-overlay.json" x')
    [ "$result" = "true" ]
}

@test "workpc: overlay JSON is valid" {
    overlay=$(nix_eval_json_apply \
        "$WORKPC_CONFIG.home.file.\".openclaw/nix-overlay.json\".text" \
        'x: builtins.fromJSON x')
    [ "$?" -eq 0 ]
    echo "$overlay" | jq -e '.agents.list' > /dev/null
}

@test "workpc: overlay JSON has gateway config" {
    overlay=$(nix_eval_json_apply \
        "$WORKPC_CONFIG.home.file.\".openclaw/nix-overlay.json\".text" \
        'x: builtins.fromJSON x')
    echo "$overlay" | jq -e '.gateway.port == 18790' > /dev/null
    echo "$overlay" | jq -e '.gateway.mode == "local"' > /dev/null
}

# ---------- Agent defaults ----------

@test "agent: default model is opus when not specified" {
    result=$(nix_eval_json "$WORKPC_OC.agents.robson.model.primary")
    [ "$result" = '"anthropic/claude-opus-4-6"' ]
}

@test "agent: default TTS engine is edge-tts" {
    result=$(nix_eval_json "$WORKPC_OC.agents.robson.tts.engine")
    [ "$result" = '"edge-tts"' ]
}

@test "agent: default telegram policies" {
    result=$(nix_eval_json "$WORKPC_OC.agents.robson.telegram.dmPolicy")
    [ "$result" = '"pairing"' ]
    result=$(nix_eval_json "$WORKPC_OC.agents.robson.telegram.groupPolicy")
    [ "$result" = '"allowlist"' ]
    result=$(nix_eval_json "$WORKPC_OC.agents.robson.telegram.streamMode")
    [ "$result" = '"off"' ]
}

@test "agent: default skills list is empty" {
    result=$(nix_eval_json "$WORKPC_OC.agents.jenny.skills")
    [ "$result" = "[]" ]
}

@test "agent: default fallbacks list is empty" {
    result=$(nix_eval_json "$WORKPC_OC.agents.jenny.model.fallbacks")
    [ "$result" = "[]" ]
}

# ---------- Cross-config consistency ----------

@test "both: memory sync configured on both machines" {
    workpc=$(nix_eval_json "$WORKPC_OC.memorySync.enable")
    nixos=$(nix_eval_json "$NIXOS_OC.memorySync.enable")
    [ "$workpc" = "true" ]
    [ "$nixos" = "true" ]
}

@test "both: jarvis only declared on nixos" {
    nixos=$(nix_eval_json "$NIXOS_OC.agents.jarvis.enable")
    [ "$nixos" = "true" ]
    run nix_eval_json "$WORKPC_OC.agents.jarvis.enable"
    [ "$status" -ne 0 ]
}

# ---------- Plugin configuration ----------

@test "workpc: plugins allow list includes hindsight-openclaw" {
    result=$(nix_eval_json "$WORKPC_OC.configPatches.\".plugins.allow\"")
    echo "$result" | jq -e 'index("hindsight-openclaw")' > /dev/null
}

@test "workpc: plugins memory slot is hindsight-openclaw" {
    result=$(nix_eval_json "$WORKPC_OC.configPatches.\".plugins.slots.memory\"")
    [ "$result" = '"hindsight-openclaw"' ]
}

@test "workpc: hindsight plugin is enabled with claude-code provider" {
    result=$(nix_eval_json "$WORKPC_OC.configPatches.\".plugins.entries.hindsight-openclaw\"")
    echo "$result" | jq -e '.enabled == true' > /dev/null
    echo "$result" | jq -e '.config.llmProvider == "claude-code"' > /dev/null
}

@test "workpc: memory-core plugin is disabled" {
    result=$(nix_eval_json "$WORKPC_OC.configPatches.\".plugins.entries.memory-core\"")
    echo "$result" | jq -e '.enabled == false' > /dev/null
}

@test "workpc: plugins allow list includes discord" {
    result=$(nix_eval_json "$WORKPC_OC.configPatches.\".plugins.allow\"")
    echo "$result" | jq -e 'index("discord")' > /dev/null
}
