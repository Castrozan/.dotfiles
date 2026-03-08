{
  pkgs,
  lib,
  inputs,
  self,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../tests/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  workpcCfg = self.homeConfigurations."lucas.zanoni@x86_64-linux".config;
  nixosCfg = self.nixosConfigurations.zanoni.config.home-manager.users.zanoni;
  workpcOc = workpcCfg.openclaw;
  nixosOc = nixosCfg.openclaw;

  workpcEnabledAgents = builtins.attrNames workpcOc.enabledAgents;
  nixosEnabledAgents = builtins.attrNames nixosOc.enabledAgents;
  workpcServiceNames = builtins.attrNames workpcCfg.systemd.user.services;
  workpcTimerNames = builtins.attrNames workpcCfg.systemd.user.timers;
  workpcConfigPatches = workpcOc.configPatches;
  nixosConfigPatches = nixosOc.configPatches;

  hasInList = list: item: builtins.elem item list;
  hasInAttr = set: key: builtins.hasAttr key set;

  workpcAgentListIds = map (a: a.id) workpcConfigPatches.".agents.list";
  nixosAgentListIds = map (a: a.id) nixosConfigPatches.".agents.list";
  workpcConfigPatchKeys = builtins.attrNames workpcConfigPatches;
  nixosConfigPatchKeys = builtins.attrNames nixosConfigPatches;
  workpcSecretPatchKeys = builtins.attrNames workpcOc.secretPatches;
  nixosSecretPatchKeys = builtins.attrNames nixosOc.secretPatches;
  workpcBindingAgentIds = map (b: b.agentId) workpcConfigPatches.".bindings";
  nixosBindingAgentIds =
    if builtins.hasAttr ".bindings" nixosConfigPatches then
      map (b: b.agentId) nixosConfigPatches.".bindings"
    else
      [ ];

  workpcOverlayContent = builtins.fromJSON workpcCfg.home.file.".openclaw/nix-overlay.json".text;

  robsonAllowAgents =
    let
      robsonEntry = builtins.head (
        builtins.filter (a: a.id == "robson") workpcConfigPatches.".agents.list"
      );
    in
    robsonEntry.subagents.allowAgents;

  jarvisAllowAgents =
    let
      jarvisEntry = builtins.head (
        builtins.filter (a: a.id == "jarvis") nixosConfigPatches.".agents.list"
      );
    in
    jarvisEntry.subagents.allowAgents;
in
{
  oc-flake-home-config-evaluates = mkEvalCheck "oc-flake-home-config-evaluates" (
    builtins.length workpcEnabledAgents > 0
  ) "homeConfiguration should evaluate with enabled agents";

  oc-flake-nixos-config-evaluates = mkEvalCheck "oc-flake-nixos-config-evaluates" (
    builtins.length nixosEnabledAgents > 0
  ) "nixosConfiguration should evaluate with enabled agents";

  oc-workpc-enabled-agents =
    mkEvalCheck "oc-workpc-enabled-agents"
      (
        hasInList workpcEnabledAgents "robson"
        && hasInList workpcEnabledAgents "jenny"
        && hasInList workpcEnabledAgents "monster"
        && hasInList workpcEnabledAgents "silver"
      )
      "workpc should have robson jenny monster silver, got: ${builtins.concatStringsSep ", " workpcEnabledAgents}";

  oc-workpc-default-agent = mkEvalCheck "oc-workpc-default-agent" (
    workpcOc.defaultAgent == "robson"
  ) "workpc default agent should be robson, got ${workpcOc.defaultAgent}";

  oc-workpc-robson-is-default =
    mkEvalCheck "oc-workpc-robson-is-default" workpcOc.agents.robson.isDefault
      "robson should be marked as default on workpc";

  oc-nixos-enabled-agents =
    mkEvalCheck "oc-nixos-enabled-agents"
      (
        hasInList nixosEnabledAgents "clever"
        && hasInList nixosEnabledAgents "golden"
        && hasInList nixosEnabledAgents "jarvis"
      )
      "nixos should have clever golden jarvis, got: ${builtins.concatStringsSep ", " nixosEnabledAgents}";

  oc-nixos-default-agent = mkEvalCheck "oc-nixos-default-agent" (
    nixosOc.defaultAgent == "clever"
  ) "nixos default agent should be clever, got ${nixosOc.defaultAgent}";

  oc-nixos-jarvis-telegram-enabled =
    mkEvalCheck "oc-nixos-jarvis-telegram-enabled" nixosOc.agents.jarvis.telegram.enable
      "jarvis telegram should be enabled";

  oc-nixos-jarvis-telegram-bot-name = mkEvalCheck "oc-nixos-jarvis-telegram-bot-name" (
    nixosOc.agents.jarvis.telegram.botName == "Jarvis"
  ) "jarvis telegram bot name should be Jarvis, got ${nixosOc.agents.jarvis.telegram.botName}";

  oc-nixos-clever-is-default =
    mkEvalCheck "oc-nixos-clever-is-default" nixosOc.agents.clever.isDefault
      "clever should be marked as default on nixos";

  oc-workpc-gateway-port = mkEvalCheck "oc-workpc-gateway-port" (
    workpcConfigPatches.".gateway.port" == 18790
  ) "workpc gateway port should be 18790, got ${toString workpcConfigPatches.".gateway.port"}";

  oc-workpc-agents-list-has-all = mkEvalCheck "oc-workpc-agents-list-has-all" (
    hasInList workpcAgentListIds "robson"
    && hasInList workpcAgentListIds "jenny"
    && hasInList workpcAgentListIds "monster"
    && hasInList workpcAgentListIds "silver"
  ) "agents list should include robson jenny monster silver";

  oc-workpc-agents-list-robson-default =
    let
      defaultAgents = builtins.filter (a: a.default or false) workpcConfigPatches.".agents.list";
      defaultId = if builtins.length defaultAgents > 0 then (builtins.head defaultAgents).id else "none";
    in
    mkEvalCheck "oc-workpc-agents-list-robson-default" (
      defaultId == "robson"
    ) "agents list should mark robson as default, got ${defaultId}";

  oc-workpc-agents-list-workspace-path =
    let
      robsonEntries = builtins.filter (a: a.id == "robson") workpcConfigPatches.".agents.list";
      robsonWorkspace =
        if builtins.length robsonEntries > 0 then (builtins.head robsonEntries).workspace else "none";
    in
    mkEvalCheck "oc-workpc-agents-list-workspace-path" (
      robsonWorkspace == "/home/lucas.zanoni/openclaw/robson"
    ) "robson workspace should be /home/lucas.zanoni/openclaw/robson, got ${robsonWorkspace}";

  oc-workpc-telegram-accounts = mkEvalCheck "oc-workpc-telegram-accounts" (
    hasInList workpcConfigPatchKeys ".channels.telegram.accounts.robson"
    && hasInList workpcConfigPatchKeys ".channels.telegram.accounts.jenny"
    && hasInList workpcConfigPatchKeys ".channels.telegram.accounts.monster"
    && hasInList workpcConfigPatchKeys ".channels.telegram.accounts.silver"
  ) "workpc should have telegram accounts for robson jenny monster silver";

  oc-workpc-no-jarvis-telegram = mkEvalCheck "oc-workpc-no-jarvis-telegram" (
    !(hasInList workpcConfigPatchKeys ".channels.telegram.accounts.jarvis")
  ) "workpc should NOT have telegram account for jarvis";

  oc-workpc-bindings-telegram-agents = mkEvalCheck "oc-workpc-bindings-telegram-agents" (
    hasInList workpcBindingAgentIds "robson"
    && hasInList workpcBindingAgentIds "jenny"
    && hasInList workpcBindingAgentIds "monster"
    && hasInList workpcBindingAgentIds "silver"
  ) "workpc bindings should include robson jenny monster silver";

  oc-workpc-no-jarvis-binding = mkEvalCheck "oc-workpc-no-jarvis-binding" (
    !(hasInList workpcBindingAgentIds "jarvis")
  ) "workpc should NOT have binding for jarvis";

  oc-workpc-gateway-mode-local = mkEvalCheck "oc-workpc-gateway-mode-local" (
    workpcConfigPatches.".gateway.mode" == "local"
  ) "workpc gateway mode should be local, got ${workpcConfigPatches.".gateway.mode"}";

  oc-workpc-compaction-mode-safeguard =
    mkEvalCheck "oc-workpc-compaction-mode-safeguard"
      (workpcConfigPatches.".agents.defaults.compaction.mode" == "safeguard")
      "compaction mode should be safeguard, got ${
        workpcConfigPatches.".agents.defaults.compaction.mode"
      }";

  oc-workpc-memory-search-enabled =
    mkEvalCheck "oc-workpc-memory-search-enabled"
      workpcConfigPatches.".agents.defaults.memorySearch.enabled"
      "memory search should be enabled";

  oc-nixos-gateway-port = mkEvalCheck "oc-nixos-gateway-port" (
    nixosConfigPatches.".gateway.port" == 18789
  ) "nixos gateway port should be 18789, got ${toString nixosConfigPatches.".gateway.port"}";

  oc-nixos-telegram-accounts = mkEvalCheck "oc-nixos-telegram-accounts" (
    hasInList nixosConfigPatchKeys ".channels.telegram.accounts.clever"
    && hasInList nixosConfigPatchKeys ".channels.telegram.accounts.golden"
    && hasInList nixosConfigPatchKeys ".channels.telegram.accounts.jarvis"
  ) "nixos should have telegram accounts for clever golden jarvis";

  oc-nixos-jarvis-telegram-account-name = mkEvalCheck "oc-nixos-jarvis-telegram-account-name" (
    nixosConfigPatches.".channels.telegram.accounts.jarvis".name == "Jarvis"
  ) "jarvis telegram account name should be Jarvis";

  oc-nixos-clever-telegram-account-name = mkEvalCheck "oc-nixos-clever-telegram-account-name" (
    nixosConfigPatches.".channels.telegram.accounts.clever".name == "Clever"
  ) "clever telegram account should use default capitalized name";

  oc-workpc-secret-gateway-auth-token =
    mkEvalCheck "oc-workpc-secret-gateway-auth-token"
      (hasInList workpcSecretPatchKeys ".gateway.auth.token")
      "secret patches should include gateway auth token";

  oc-workpc-gateway-token-path-agenix =
    let
      tokenPath = workpcOc.secretPatches.".gateway.auth.token";
    in
    mkEvalCheck "oc-workpc-gateway-token-path-agenix" (
      builtins.match ".*\\.secrets/.*" tokenPath != null
    ) "gateway token path should be agenix managed, got ${tokenPath}";

  oc-workpc-telegram-bot-token-secrets = mkEvalCheck "oc-workpc-telegram-bot-token-secrets" (
    hasInList workpcSecretPatchKeys ".channels.telegram.accounts.robson.botToken"
    && hasInList workpcSecretPatchKeys ".channels.telegram.accounts.jenny.botToken"
    && hasInList workpcSecretPatchKeys ".channels.telegram.accounts.monster.botToken"
    && hasInList workpcSecretPatchKeys ".channels.telegram.accounts.silver.botToken"
  ) "workpc should have telegram bot token secrets for enabled agents";

  oc-workpc-no-jarvis-bot-token = mkEvalCheck "oc-workpc-no-jarvis-bot-token" (
    !(hasInList workpcSecretPatchKeys ".channels.telegram.accounts.jarvis.botToken")
  ) "workpc should NOT have jarvis bot token secret";

  oc-nixos-secret-path-agenix =
    let
      tokenPath = nixosOc.secretPatches.".gateway.auth.token";
    in
    mkEvalCheck "oc-nixos-secret-path-agenix" (
      builtins.match ".*\\.secrets/.*" tokenPath != null
    ) "nixos secret path should use secrets file, got ${tokenPath}";

  oc-nixos-jarvis-bot-token-secret =
    mkEvalCheck "oc-nixos-jarvis-bot-token-secret"
      (hasInList nixosSecretPatchKeys ".channels.telegram.accounts.jarvis.botToken")
      "nixos should have jarvis bot token secret";

  oc-workpc-default-primary-model =
    mkEvalCheck "oc-workpc-default-primary-model"
      (workpcConfigPatches.".agents.defaults.model.primary" == "anthropic/claude-opus-4-6")
      "default primary model should be anthropic/claude-opus-4-6, got ${
        workpcConfigPatches.".agents.defaults.model.primary"
      }";

  oc-workpc-model-aliases =
    let
      modelKeys = builtins.attrNames workpcConfigPatches.".agents.defaults.models";
    in
    mkEvalCheck "oc-workpc-model-aliases"
      (
        hasInList modelKeys "anthropic/claude-opus-4-6"
        && hasInList modelKeys "anthropic/claude-sonnet-4-6"
        && hasInList modelKeys "openai-codex/gpt-5.3-codex"
      )
      "model aliases should include opus sonnet codex, got: ${builtins.concatStringsSep ", " modelKeys}";

  oc-workpc-gateway-service-defined =
    mkEvalCheck "oc-workpc-gateway-service-defined" (hasInList workpcServiceNames "openclaw-gateway")
      "gateway service should be defined";

  oc-workpc-gateway-restart-policy = mkEvalCheck "oc-workpc-gateway-restart-policy" (
    workpcCfg.systemd.user.services.openclaw-gateway.Service.Restart == "always"
  ) "gateway restart policy should be always";

  oc-workpc-gateway-env-nix-mode =
    let
      env = workpcCfg.systemd.user.services.openclaw-gateway.Service.Environment;
      hasNixMode = builtins.any (e: builtins.match "OPENCLAW_NIX_MODE.*" e != null) env;
    in
    mkEvalCheck "oc-workpc-gateway-env-nix-mode" hasNixMode
      "gateway environment should have OPENCLAW_NIX_MODE";

  oc-workpc-gateway-env-node-production =
    let
      env = workpcCfg.systemd.user.services.openclaw-gateway.Service.Environment;
    in
    mkEvalCheck "oc-workpc-gateway-env-node-production" (hasInList env "NODE_ENV=production")
      "gateway environment should have NODE_ENV=production";

  oc-workpc-gateway-path-includes-bin =
    let
      env = workpcCfg.systemd.user.services.openclaw-gateway.Service.Environment;
      pathEntries = builtins.filter (e: builtins.match "PATH=.*" e != null) env;
      pathEntry = if builtins.length pathEntries > 0 then builtins.head pathEntries else "";
    in
    mkEvalCheck "oc-workpc-gateway-path-includes-bin" (
      builtins.match ".*(/bin).*" pathEntry != null
    ) "gateway PATH should include /bin";

  oc-workpc-gateway-wanted-by-default =
    mkEvalCheck "oc-workpc-gateway-wanted-by-default"
      (hasInList workpcCfg.systemd.user.services.openclaw-gateway.Install.WantedBy "default.target")
      "gateway should be wanted by default.target";

  oc-workpc-memory-sync-service-defined =
    mkEvalCheck "oc-workpc-memory-sync-service-defined"
      (hasInList workpcServiceNames "openclaw-memory-sync")
      "memory sync service should be defined";

  oc-workpc-memory-sync-timer-defined =
    mkEvalCheck "oc-workpc-memory-sync-timer-defined"
      (hasInList workpcTimerNames "openclaw-memory-sync")
      "memory sync timer should be defined";

  oc-workpc-memory-sync-oneshot = mkEvalCheck "oc-workpc-memory-sync-oneshot" (
    workpcCfg.systemd.user.services.openclaw-memory-sync.Service.Type == "oneshot"
  ) "memory sync service should be oneshot";

  oc-workpc-memory-sync-timer-wanted-by =
    mkEvalCheck "oc-workpc-memory-sync-timer-wanted-by"
      (hasInList workpcCfg.systemd.user.timers.openclaw-memory-sync.Install.WantedBy "timers.target")
      "memory sync timer should be wanted by timers.target";

  oc-workpc-memory-sync-agents = mkEvalCheck "oc-workpc-memory-sync-agents" (
    hasInList workpcOc.memorySync.agents "robson"
    && hasInList workpcOc.memorySync.agents "jenny"
    && hasInList workpcOc.memorySync.agents "monster"
    && hasInList workpcOc.memorySync.agents "silver"
  ) "memory sync should be configured for local agents";

  oc-workpc-memory-sync-remote-host = mkEvalCheck "oc-workpc-memory-sync-remote-host" (
    workpcOc.memorySync.remoteHost == "dellg15"
  ) "workpc memory sync remote host should be dellg15, got ${workpcOc.memorySync.remoteHost}";

  oc-nixos-memory-sync-remote-host = mkEvalCheck "oc-nixos-memory-sync-remote-host" (
    nixosOc.memorySync.remoteHost == "workpc"
  ) "nixos memory sync remote host should be workpc, got ${nixosOc.memorySync.remoteHost}";

  oc-workpc-overlay-json-exists =
    mkEvalCheck "oc-workpc-overlay-json-exists"
      (builtins.hasAttr ".openclaw/nix-overlay.json" workpcCfg.home.file)
      "nix-overlay.json should be generated";

  oc-workpc-overlay-json-valid =
    mkEvalCheck "oc-workpc-overlay-json-valid" (builtins.hasAttr "list" workpcOverlayContent.agents)
      "overlay JSON should be valid with agents.list";

  oc-workpc-overlay-gateway-config = mkEvalCheck "oc-workpc-overlay-gateway-config" (
    workpcOverlayContent.gateway.port == 18790 && workpcOverlayContent.gateway.mode == "local"
  ) "overlay JSON should have correct gateway config";

  oc-agent-model-primary-set = mkEvalCheck "oc-agent-model-primary-set" (
    workpcOc.agents.robson.model.primary != null && workpcOc.agents.robson.model.primary != ""
  ) "robson model.primary should be set";

  oc-agent-silver-cheaper-model = mkEvalCheck "oc-agent-silver-cheaper-model" (
    workpcOc.agents.silver.model.primary == "anthropic/claude-sonnet-4-6"
  ) "silver should use cheaper model, got ${workpcOc.agents.silver.model.primary}";

  oc-agent-golden-cheaper-model = mkEvalCheck "oc-agent-golden-cheaper-model" (
    nixosOc.agents.golden.model.primary == "anthropic/claude-sonnet-4-6"
  ) "golden should use cheaper model, got ${nixosOc.agents.golden.model.primary}";

  oc-agent-default-tts-engine = mkEvalCheck "oc-agent-default-tts-engine" (
    workpcOc.agents.robson.tts.engine == "edge-tts"
  ) "default TTS engine should be edge-tts, got ${workpcOc.agents.robson.tts.engine}";

  oc-agent-default-telegram-policies = mkEvalCheck "oc-agent-default-telegram-policies" (
    workpcOc.agents.robson.telegram.dmPolicy == "pairing"
    && workpcOc.agents.robson.telegram.groupPolicy == "allowlist"
    && workpcOc.agents.robson.telegram.streamMode == "partial"
  ) "default telegram policies should be pairing/allowlist/partial";

  oc-agent-default-skills-empty = mkEvalCheck "oc-agent-default-skills-empty" (
    workpcOc.agents.jenny.skills == [ ]
  ) "default skills list should be empty";

  oc-agent-default-fallbacks-empty = mkEvalCheck "oc-agent-default-fallbacks-empty" (
    workpcOc.agents.jenny.model.fallbacks == [ ]
  ) "default fallbacks list should be empty";

  oc-both-memory-sync-configured = mkEvalCheck "oc-both-memory-sync-configured" (
    workpcOc.memorySync.enable && nixosOc.memorySync.enable
  ) "memory sync should be configured on both machines";

  oc-both-jarvis-only-nixos = mkEvalCheck "oc-both-jarvis-only-nixos" (
    nixosOc.agents.jarvis.enable && !(workpcOc.agents ? jarvis)
  ) "jarvis should only be declared on nixos";

  oc-workpc-plugins-allow-memory-core = mkEvalCheck "oc-workpc-plugins-allow-memory-core" (hasInList
    workpcConfigPatches.".plugins.allow"
    "memory-core"
  ) "plugins allow list should include memory-core";

  oc-workpc-plugins-memory-slot = mkEvalCheck "oc-workpc-plugins-memory-slot" (
    workpcConfigPatches.".plugins.slots.memory" == "memory-core"
  ) "plugins memory slot should be memory-core";

  oc-workpc-memory-core-enabled =
    mkEvalCheck "oc-workpc-memory-core-enabled"
      workpcConfigPatches.".plugins.entries.memory-core".enabled
      "memory-core plugin should be enabled";

  oc-workpc-hindsight-in-config-deletes =
    mkEvalCheck "oc-workpc-hindsight-in-config-deletes"
      (hasInList workpcOc.configDeletes ".plugins.entries.hindsight-openclaw")
      "hindsight-openclaw should be in configDeletes";

  oc-workpc-plugins-allow-discord = mkEvalCheck "oc-workpc-plugins-allow-discord" (hasInList
    workpcConfigPatches.".plugins.allow"
    "discord"
  ) "plugins allow list should include discord";

  oc-nixos-agent-to-agent-enabled =
    mkEvalCheck "oc-nixos-agent-to-agent-enabled" nixosConfigPatches.".tools.agentToAgent.enabled"
      "nixos agentToAgent should be enabled";

  oc-nixos-agent-to-agent-allow-list = mkEvalCheck "oc-nixos-agent-to-agent-allow-list" (
    hasInList nixosConfigPatches.".tools.agentToAgent.allow" "clever"
    && hasInList nixosConfigPatches.".tools.agentToAgent.allow" "golden"
    && hasInList nixosConfigPatches.".tools.agentToAgent.allow" "jarvis"
  ) "nixos agentToAgent allow list should include clever golden jarvis";

  oc-nixos-sessions-visibility = mkEvalCheck "oc-nixos-sessions-visibility" (
    nixosConfigPatches.".tools.sessions.visibility" == "all"
  ) "nixos sessions visibility should be all";

  oc-nixos-jarvis-allow-agents-has-entries = mkEvalCheck "oc-nixos-jarvis-allow-agents-has-entries" (
    builtins.length jarvisAllowAgents > 0
  ) "jarvis should have allowAgents entries";

  oc-nixos-jarvis-allow-agents-includes-clever-golden =
    mkEvalCheck "oc-nixos-jarvis-allow-agents-includes-clever-golden"
      (hasInList jarvisAllowAgents "clever" && hasInList jarvisAllowAgents "golden")
      "jarvis allowAgents should include clever and golden";

  oc-nixos-jarvis-allow-agents-excludes-self =
    mkEvalCheck "oc-nixos-jarvis-allow-agents-excludes-self" (!(hasInList jarvisAllowAgents "jarvis"))
      "jarvis allowAgents should NOT include jarvis itself";

  oc-workpc-agent-to-agent-enabled =
    mkEvalCheck "oc-workpc-agent-to-agent-enabled" workpcConfigPatches.".tools.agentToAgent.enabled"
      "workpc agentToAgent should be enabled";

  oc-workpc-agent-to-agent-allow-list = mkEvalCheck "oc-workpc-agent-to-agent-allow-list" (
    hasInList workpcConfigPatches.".tools.agentToAgent.allow" "robson"
    && hasInList workpcConfigPatches.".tools.agentToAgent.allow" "jenny"
    && hasInList workpcConfigPatches.".tools.agentToAgent.allow" "monster"
    && hasInList workpcConfigPatches.".tools.agentToAgent.allow" "silver"
  ) "workpc agentToAgent allow list should include robson jenny monster silver";

  oc-workpc-sessions-visibility = mkEvalCheck "oc-workpc-sessions-visibility" (
    workpcConfigPatches.".tools.sessions.visibility" == "all"
  ) "workpc sessions visibility should be all";

  oc-workpc-robson-allow-agents = mkEvalCheck "oc-workpc-robson-allow-agents" (
    hasInList robsonAllowAgents "jenny" && hasInList robsonAllowAgents "monster"
  ) "robson allowAgents should include jenny and monster";
}
