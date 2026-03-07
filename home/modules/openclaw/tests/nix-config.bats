#!/usr/bin/env bats

setup_file() {
    REPO_DIR="$(cd "$BATS_TEST_DIRNAME" && git rev-parse --show-toplevel)"
    load "$REPO_DIR/tests/helpers/test-status-tracker.bash"
    _initialize_test_status_tracking
    _evaluate_all_openclaw_test_data
}

setup() {
    REPO_DIR="$(cd "$BATS_TEST_DIRNAME" && git rev-parse --show-toplevel)"
    load "$REPO_DIR/tests/helpers/test-status-tracker.bash"
    ALL_CONFIG="$BATS_FILE_TMPDIR/all-config.json"
}

teardown() {
    _record_test_failure_if_any
}

teardown_file() {
    _write_passing_status_if_all_passed
}

_evaluate_all_openclaw_test_data() {
    nix eval --impure --json --expr '
      let
        flake = builtins.getFlake (toString '"$REPO_DIR"');
        workpcCfg = flake.homeConfigurations."lucas.zanoni@x86_64-linux".config;
        nixosCfg = flake.nixosConfigurations.zanoni.config.home-manager.users.zanoni;
        workpcOc = workpcCfg.openclaw;
        nixosOc = nixosCfg.openclaw;
      in {
        workpc = {
          enabledAgents = builtins.attrNames workpcOc.enabledAgents;
          defaultAgent = workpcOc.defaultAgent;
          configPatches = workpcOc.configPatches;
          secretPatches = workpcOc.secretPatches;
          configDeletes = workpcOc.configDeletes;
          memorySync = { inherit (workpcOc.memorySync) enable agents remoteHost; };
          agents = {
            robson = {
              isDefault = workpcOc.agents.robson.isDefault;
              modelPrimary = workpcOc.agents.robson.model.primary;
              ttsEngine = workpcOc.agents.robson.tts.engine;
              telegramDmPolicy = workpcOc.agents.robson.telegram.dmPolicy;
              telegramGroupPolicy = workpcOc.agents.robson.telegram.groupPolicy;
              telegramStreamMode = workpcOc.agents.robson.telegram.streamMode;
            };
            silver = { modelPrimary = workpcOc.agents.silver.model.primary; };
            jenny = {
              skills = workpcOc.agents.jenny.skills;
              modelFallbacks = workpcOc.agents.jenny.model.fallbacks;
            };
            hasJarvis = workpcOc.agents ? jarvis;
          };
          systemd = {
            serviceNames = builtins.attrNames workpcCfg.systemd.user.services;
            timerNames = builtins.attrNames workpcCfg.systemd.user.timers;
            gatewayRestart = workpcCfg.systemd.user.services.openclaw-gateway.Service.Restart;
            gatewayEnvironment = workpcCfg.systemd.user.services.openclaw-gateway.Service.Environment;
            gatewayWantedBy = workpcCfg.systemd.user.services.openclaw-gateway.Install.WantedBy;
            memorySyncType = workpcCfg.systemd.user.services.openclaw-memory-sync.Service.Type;
            memorySyncTimerWantedBy = workpcCfg.systemd.user.timers.openclaw-memory-sync.Install.WantedBy;
          };
          overlayExists = builtins.hasAttr ".openclaw/nix-overlay.json" workpcCfg.home.file;
          overlayContent = builtins.fromJSON workpcCfg.home.file.".openclaw/nix-overlay.json".text;
        };
        nixos = {
          enabledAgents = builtins.attrNames nixosOc.enabledAgents;
          defaultAgent = nixosOc.defaultAgent;
          configPatches = nixosOc.configPatches;
          secretPatches = nixosOc.secretPatches;
          memorySync = { inherit (nixosOc.memorySync) enable remoteHost; };
          agents = {
            clever = { isDefault = nixosOc.agents.clever.isDefault; };
            golden = { modelPrimary = nixosOc.agents.golden.model.primary; };
            jarvis = {
              enable = nixosOc.agents.jarvis.enable;
              telegramEnable = nixosOc.agents.jarvis.telegram.enable;
              telegramBotName = nixosOc.agents.jarvis.telegram.botName;
            };
          };
        };
      }
    ' 2>/dev/null > "$BATS_FILE_TMPDIR/all-config.json"

    [ -s "$BATS_FILE_TMPDIR/all-config.json" ] || {
        echo "Failed to evaluate openclaw test data" >&2
        return 1
    }
}

# ---------- Flake evaluation ----------

@test "flake: homeConfiguration evaluates without errors" {
    jq -e '.workpc.enabledAgents | length > 0' "$ALL_CONFIG" > /dev/null
}

@test "flake: nixosConfiguration evaluates without errors" {
    jq -e '.nixos.enabledAgents | length > 0' "$ALL_CONFIG" > /dev/null
}

# ---------- Agent configuration (workpc) ----------

@test "workpc: enabled agents include robson jenny monster silver" {
    for agent in robson jenny monster silver; do
        jq -e ".workpc.enabledAgents | index(\"$agent\")" "$ALL_CONFIG" > /dev/null
    done
}

@test "workpc: default agent is robson" {
    [ "$(jq -r '.workpc.defaultAgent' "$ALL_CONFIG")" = "robson" ]
}

@test "workpc: robson is marked as default" {
    [ "$(jq '.workpc.agents.robson.isDefault' "$ALL_CONFIG")" = "true" ]
}

# ---------- Agent configuration (NixOS) ----------

@test "nixos: enabled agents include clever golden jarvis" {
    for agent in clever golden jarvis; do
        jq -e ".nixos.enabledAgents | index(\"$agent\")" "$ALL_CONFIG" > /dev/null
    done
}

@test "nixos: default agent is clever" {
    [ "$(jq -r '.nixos.defaultAgent' "$ALL_CONFIG")" = "clever" ]
}

@test "nixos: jarvis telegram is enabled" {
    [ "$(jq '.nixos.agents.jarvis.telegramEnable' "$ALL_CONFIG")" = "true" ]
}

@test "nixos: jarvis telegram bot name is Jarvis" {
    [ "$(jq -r '.nixos.agents.jarvis.telegramBotName' "$ALL_CONFIG")" = "Jarvis" ]
}

@test "nixos: clever is marked as default" {
    [ "$(jq '.nixos.agents.clever.isDefault' "$ALL_CONFIG")" = "true" ]
}

# ---------- Config patches (workpc) ----------

@test "workpc: gateway port patch is 18790" {
    [ "$(jq '.workpc.configPatches[".gateway.port"]' "$ALL_CONFIG")" = "18790" ]
}

@test "workpc: agents list patch has all enabled agents" {
    result=$(jq '[.workpc.configPatches[".agents.list"][] | .id]' "$ALL_CONFIG")
    for agent in robson jenny monster silver; do
        echo "$result" | jq -e "index(\"$agent\")" > /dev/null
    done
}

@test "workpc: agents list marks robson as default" {
    jq -e '[.workpc.configPatches[".agents.list"][] | select(.default == true)][0].id == "robson"' "$ALL_CONFIG" > /dev/null
}

@test "workpc: agents list has correct workspace paths" {
    jq -e '[.workpc.configPatches[".agents.list"][] | select(.id == "robson")][0].workspace == "/home/lucas.zanoni/openclaw/robson"' "$ALL_CONFIG" > /dev/null
}

@test "workpc: telegram accounts include robson jenny monster silver" {
    result=$(jq '.workpc.configPatches | keys' "$ALL_CONFIG")
    for agent in robson jenny monster silver; do
        echo "$result" | jq -e "index(\".channels.telegram.accounts.$agent\")" > /dev/null
    done
}

@test "workpc: no telegram account for jarvis" {
    run jq -e '.workpc.configPatches | keys | index(".channels.telegram.accounts.jarvis")' "$ALL_CONFIG"
    [ "$status" -ne 0 ]
}

@test "workpc: bindings exist for telegram-enabled agents" {
    result=$(jq '[.workpc.configPatches[".bindings"][] | .agentId]' "$ALL_CONFIG")
    for agent in robson jenny monster silver; do
        echo "$result" | jq -e "index(\"$agent\")" > /dev/null
    done
}

@test "workpc: no binding for jarvis" {
    run jq -e '[.workpc.configPatches[".bindings"][] | .agentId] | index("jarvis")' "$ALL_CONFIG"
    [ "$status" -ne 0 ]
}

@test "workpc: gateway mode is local" {
    [ "$(jq -r '.workpc.configPatches[".gateway.mode"]' "$ALL_CONFIG")" = "local" ]
}

@test "workpc: compaction mode is safeguard" {
    [ "$(jq -r '.workpc.configPatches[".agents.defaults.compaction.mode"]' "$ALL_CONFIG")" = "safeguard" ]
}

@test "workpc: memory search is enabled" {
    [ "$(jq '.workpc.configPatches[".agents.defaults.memorySearch.enabled"]' "$ALL_CONFIG")" = "true" ]
}

# ---------- Config patches (NixOS) ----------

@test "nixos: gateway port patch is 18789" {
    [ "$(jq '.nixos.configPatches[".gateway.port"]' "$ALL_CONFIG")" = "18789" ]
}

@test "nixos: telegram accounts include clever golden jarvis" {
    result=$(jq '.nixos.configPatches | keys' "$ALL_CONFIG")
    for agent in clever golden jarvis; do
        echo "$result" | jq -e "index(\".channels.telegram.accounts.$agent\")" > /dev/null
    done
}

@test "nixos: jarvis telegram account name is Jarvis" {
    jq -e '.nixos.configPatches[".channels.telegram.accounts.jarvis"].name == "Jarvis"' "$ALL_CONFIG" > /dev/null
}

@test "nixos: clever telegram account uses default capitalized name" {
    jq -e '.nixos.configPatches[".channels.telegram.accounts.clever"].name == "Clever"' "$ALL_CONFIG" > /dev/null
}

# ---------- Secret patches ----------

@test "workpc: secret patches include gateway auth token" {
    jq -e '.workpc.secretPatches | keys | index(".gateway.auth.token")' "$ALL_CONFIG" > /dev/null
}

@test "workpc: gateway token path is agenix managed" {
    result=$(jq -r '.workpc.secretPatches[".gateway.auth.token"]' "$ALL_CONFIG")
    [[ "$result" == *".secrets/"* ]]
}

@test "workpc: telegram bot token secrets for enabled telegram agents" {
    result=$(jq '.workpc.secretPatches | keys' "$ALL_CONFIG")
    for agent in robson jenny monster silver; do
        echo "$result" | jq -e "index(\".channels.telegram.accounts.$agent.botToken\")" > /dev/null
    done
}

@test "workpc: no telegram bot token secret for jarvis" {
    run jq -e '.workpc.secretPatches | keys | index(".channels.telegram.accounts.jarvis.botToken")' "$ALL_CONFIG"
    [ "$status" -ne 0 ]
}

@test "nixos: secret patches use secrets file paths" {
    result=$(jq -r '.nixos.secretPatches[".gateway.auth.token"]' "$ALL_CONFIG")
    [[ "$result" == *".secrets/"* ]]
}

@test "nixos: telegram bot token secret for jarvis exists" {
    jq -e '.nixos.secretPatches | keys | index(".channels.telegram.accounts.jarvis.botToken")' "$ALL_CONFIG" > /dev/null
}

# ---------- Default model configuration ----------

@test "workpc: default primary model is opus" {
    [ "$(jq -r '.workpc.configPatches[".agents.defaults.model.primary"]' "$ALL_CONFIG")" = "anthropic/claude-opus-4-6" ]
}

@test "workpc: model aliases include opus sonnet codex" {
    result=$(jq '.workpc.configPatches[".agents.defaults.models"] | keys' "$ALL_CONFIG")
    echo "$result" | jq -e 'index("anthropic/claude-opus-4-6")' > /dev/null
    echo "$result" | jq -e 'index("anthropic/claude-sonnet-4-6")' > /dev/null
    echo "$result" | jq -e 'index("openai-codex/gpt-5.3-codex")' > /dev/null
}

# ---------- Gateway service ----------

@test "workpc: gateway service is defined" {
    jq -e '.workpc.systemd.serviceNames | index("openclaw-gateway")' "$ALL_CONFIG" > /dev/null
}

@test "workpc: gateway service has correct restart policy" {
    [ "$(jq -r '.workpc.systemd.gatewayRestart' "$ALL_CONFIG")" = "always" ]
}

@test "workpc: gateway service environment has OPENCLAW_NIX_MODE" {
    jq -e '.workpc.systemd.gatewayEnvironment | map(select(startswith("OPENCLAW_NIX_MODE"))) | length > 0' "$ALL_CONFIG" > /dev/null
}

@test "workpc: gateway service environment has NODE_ENV=production" {
    jq -e '.workpc.systemd.gatewayEnvironment | index("NODE_ENV=production")' "$ALL_CONFIG" > /dev/null
}

@test "workpc: gateway service PATH includes git" {
    pathEntry=$(jq -r '.workpc.systemd.gatewayEnvironment[] | select(startswith("PATH="))' "$ALL_CONFIG")
    [[ "$pathEntry" == *"/bin"* ]]
}

@test "workpc: gateway service wanted by default.target" {
    jq -e '.workpc.systemd.gatewayWantedBy | index("default.target")' "$ALL_CONFIG" > /dev/null
}

# ---------- Memory sync ----------

@test "workpc: memory sync service is defined" {
    jq -e '.workpc.systemd.serviceNames | index("openclaw-memory-sync")' "$ALL_CONFIG" > /dev/null
}

@test "workpc: memory sync timer is defined" {
    jq -e '.workpc.systemd.timerNames | index("openclaw-memory-sync")' "$ALL_CONFIG" > /dev/null
}

@test "workpc: memory sync service is oneshot" {
    [ "$(jq -r '.workpc.systemd.memorySyncType' "$ALL_CONFIG")" = "oneshot" ]
}

@test "workpc: memory sync timer wanted by timers.target" {
    jq -e '.workpc.systemd.memorySyncTimerWantedBy | index("timers.target")' "$ALL_CONFIG" > /dev/null
}

@test "workpc: memory sync configured for local agents" {
    result=$(jq '.workpc.memorySync.agents' "$ALL_CONFIG")
    for agent in robson jenny monster silver; do
        echo "$result" | jq -e "index(\"$agent\")" > /dev/null
    done
}

@test "workpc: memory sync remote host is dellg15" {
    [ "$(jq -r '.workpc.memorySync.remoteHost' "$ALL_CONFIG")" = "dellg15" ]
}

@test "nixos: memory sync remote host is workpc" {
    [ "$(jq -r '.nixos.memorySync.remoteHost' "$ALL_CONFIG")" = "workpc" ]
}

# ---------- Overlay JSON structure ----------

@test "workpc: nix-overlay.json file is generated" {
    [ "$(jq '.workpc.overlayExists' "$ALL_CONFIG")" = "true" ]
}

@test "workpc: overlay JSON is valid" {
    jq -e '.workpc.overlayContent.agents.list' "$ALL_CONFIG" > /dev/null
}

@test "workpc: overlay JSON has gateway config" {
    jq -e '.workpc.overlayContent.gateway.port == 18790' "$ALL_CONFIG" > /dev/null
    jq -e '.workpc.overlayContent.gateway.mode == "local"' "$ALL_CONFIG" > /dev/null
}

# ---------- Agent defaults ----------

@test "agent: model.primary is set for default agent" {
    result=$(jq -r '.workpc.agents.robson.modelPrimary' "$ALL_CONFIG")
    [ "$result" != "null" ] && [ -n "$result" ]
}

@test "agent: silver model.primary is a cheaper model than default" {
    [ "$(jq -r '.workpc.agents.silver.modelPrimary' "$ALL_CONFIG")" = "anthropic/claude-sonnet-4-6" ]
}

@test "agent: golden model.primary is a cheaper model than default" {
    [ "$(jq -r '.nixos.agents.golden.modelPrimary' "$ALL_CONFIG")" = "anthropic/claude-sonnet-4-6" ]
}

@test "agent: default TTS engine is edge-tts" {
    [ "$(jq -r '.workpc.agents.robson.ttsEngine' "$ALL_CONFIG")" = "edge-tts" ]
}

@test "agent: default telegram policies" {
    [ "$(jq -r '.workpc.agents.robson.telegramDmPolicy' "$ALL_CONFIG")" = "pairing" ]
    [ "$(jq -r '.workpc.agents.robson.telegramGroupPolicy' "$ALL_CONFIG")" = "allowlist" ]
    [ "$(jq -r '.workpc.agents.robson.telegramStreamMode' "$ALL_CONFIG")" = "partial" ]
}

@test "agent: default skills list is empty" {
    [ "$(jq '.workpc.agents.jenny.skills' "$ALL_CONFIG")" = "[]" ]
}

@test "agent: default fallbacks list is empty" {
    [ "$(jq '.workpc.agents.jenny.modelFallbacks' "$ALL_CONFIG")" = "[]" ]
}

# ---------- Cross-config consistency ----------

@test "both: memory sync configured on both machines" {
    [ "$(jq '.workpc.memorySync.enable' "$ALL_CONFIG")" = "true" ]
    [ "$(jq '.nixos.memorySync.enable' "$ALL_CONFIG")" = "true" ]
}

@test "both: jarvis only declared on nixos" {
    [ "$(jq '.nixos.agents.jarvis.enable' "$ALL_CONFIG")" = "true" ]
    [ "$(jq '.workpc.agents.hasJarvis' "$ALL_CONFIG")" = "false" ]
}

# ---------- Plugin configuration ----------

@test "workpc: plugins allow list includes memory-core" {
    jq -e '.workpc.configPatches[".plugins.allow"] | index("memory-core")' "$ALL_CONFIG" > /dev/null
}

@test "workpc: plugins memory slot is memory-core" {
    [ "$(jq -r '.workpc.configPatches[".plugins.slots.memory"]' "$ALL_CONFIG")" = "memory-core" ]
}

@test "workpc: memory-core plugin is enabled" {
    jq -e '.workpc.configPatches[".plugins.entries.memory-core"].enabled == true' "$ALL_CONFIG" > /dev/null
}

@test "workpc: hindsight-openclaw is in configDeletes" {
    jq -e '.workpc.configDeletes | index(".plugins.entries.hindsight-openclaw")' "$ALL_CONFIG" > /dev/null
}

@test "workpc: plugins allow list includes discord" {
    jq -e '.workpc.configPatches[".plugins.allow"] | index("discord")' "$ALL_CONFIG" > /dev/null
}

# ---------- Inter-agent communication ----------

@test "nixos: agentToAgent is enabled" {
    [ "$(jq '.nixos.configPatches[".tools.agentToAgent.enabled"]' "$ALL_CONFIG")" = "true" ]
}

@test "nixos: agentToAgent allow list includes all enabled agents" {
    result=$(jq '.nixos.configPatches[".tools.agentToAgent.allow"]' "$ALL_CONFIG")
    for agent in clever golden jarvis; do
        echo "$result" | jq -e "index(\"$agent\")" > /dev/null
    done
}

@test "nixos: sessions visibility is all" {
    [ "$(jq -r '.nixos.configPatches[".tools.sessions.visibility"]' "$ALL_CONFIG")" = "all" ]
}

@test "nixos: agents list has subagents.allowAgents for jarvis" {
    jq -e '[.nixos.configPatches[".agents.list"][] | select(.id == "jarvis")][0].subagents.allowAgents | length > 0' "$ALL_CONFIG" > /dev/null
}

@test "nixos: jarvis allowAgents includes clever and golden" {
    result=$(jq '[.nixos.configPatches[".agents.list"][] | select(.id == "jarvis")][0].subagents.allowAgents' "$ALL_CONFIG")
    echo "$result" | jq -e 'index("clever")' > /dev/null
    echo "$result" | jq -e 'index("golden")' > /dev/null
}

@test "nixos: jarvis allowAgents does NOT include jarvis itself" {
    ! jq -e '[.nixos.configPatches[".agents.list"][] | select(.id == "jarvis")][0].subagents.allowAgents | index("jarvis")' "$ALL_CONFIG" > /dev/null
}

@test "workpc: agentToAgent is enabled" {
    [ "$(jq '.workpc.configPatches[".tools.agentToAgent.enabled"]' "$ALL_CONFIG")" = "true" ]
}

@test "workpc: agentToAgent allow list includes all enabled agents" {
    result=$(jq '.workpc.configPatches[".tools.agentToAgent.allow"]' "$ALL_CONFIG")
    for agent in robson jenny monster silver; do
        echo "$result" | jq -e "index(\"$agent\")" > /dev/null
    done
}

@test "workpc: sessions visibility is all" {
    [ "$(jq -r '.workpc.configPatches[".tools.sessions.visibility"]' "$ALL_CONFIG")" = "all" ]
}

@test "workpc: robson allowAgents includes jenny and monster" {
    result=$(jq '[.workpc.configPatches[".agents.list"][] | select(.id == "robson")][0].subagents.allowAgents' "$ALL_CONFIG")
    echo "$result" | jq -e 'index("jenny")' > /dev/null
    echo "$result" | jq -e 'index("monster")' > /dev/null
}
