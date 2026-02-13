# Declarative patches for openclaw.json.
#
# openclaw.json is app-managed — the gateway, `openclaw configure`, and
# `doctor --fix` all do full JSON overwrites, destroying any inline
# directives. On every nix rebuild, the engine in config-patch.nix applies
# these patches via jq, then writes back atomically. The app can freely
# modify the config between rebuilds; next rebuild re-pins our fields.
#
# Add/remove a pinned field = add/remove one line here.
# Engine details: see config-patch.nix.
{
  config,
  lib,
  isNixOS,
  ...
}:
let
  inherit (config) openclaw;
  homeDir = config.home.homeDirectory;

  # Generate agents list from enabled agents
  agentsList = lib.mapAttrsToList (
    name: agent:
    {
      id = name;
      workspace = "${homeDir}/${agent.workspace}";
      model = {
        inherit (agent.model) primary;
      }
      // lib.optionalAttrs (agent.model.fallbacks != [ ]) { inherit (agent.model) fallbacks; };
    }
    // lib.optionalAttrs (name == openclaw.defaultAgent) { default = true; }
  ) openclaw.enabledAgents;

  # Default workspace for agents.defaults (use default agent's workspace)
  defaultWorkspace =
    if openclaw.defaultAgent != null then
      "${homeDir}/${openclaw.agents.${openclaw.defaultAgent}.workspace}"
    else
      "${homeDir}/openclaw";

  # Get agents with telegram enabled
  telegramEnabledAgents = lib.filterAttrs (_: a: a.telegram.enable) openclaw.enabledAgents;

  # Capitalize first letter helper
  capitalize = s: lib.toUpper (lib.substring 0 1 s) + lib.substring 1 (-1) s;

  # Generate telegram accounts for agents with telegram enabled
  # Note: botToken is handled via secretPatches, not here
  telegramAccounts = lib.mapAttrs (name: agent: {
    name = if agent.telegram.botName != null then agent.telegram.botName else capitalize name;
    enabled = true;
    inherit (agent.telegram) dmPolicy groupPolicy streamMode;
  }) telegramEnabledAgents;

  # Generate bindings for telegram-enabled agents
  telegramBindings = lib.mapAttrsToList (name: _: {
    agentId = name;
    match = {
      channel = "telegram";
      accountId = name;
    };
  }) telegramEnabledAgents;
  # Base config patches
  basePatches = {
    ".tools.exec.pathPrepend" = [
      "${homeDir}/openclaw/scripts"
      "/run/current-system/sw/bin"
      "/etc/profiles/per-user/${config.home.username}/bin"
    ];
    ".agents.list" = agentsList;
    ".agents.defaults.workspace" = defaultWorkspace;
    ".agents.defaults.model.primary" = openclaw.defaults.model.primary;
    ".agents.defaults.heartbeat.model" = openclaw.defaults.model.heartbeat;
    ".agents.defaults.subagents.model" = openclaw.defaults.model.subagents;
    ".agents.defaults.model.fallbacks" = [
      "anthropic/claude-sonnet-4-5"
      "openai-codex/gpt-5.1-codex-mini"
    ];
    ".agents.defaults.models" = {
      "anthropic/claude-opus-4-6" = {
        alias = "opus";
      };
      "anthropic/claude-sonnet-4-5" = {
        alias = "sonnet";
      };
      "openai-codex/gpt-5.1-codex-mini" = {
        alias = "codex-mini";
      };
    };
    ".models.mode" = "merge";
    ".auth.profiles" = {
      "anthropic:default" = {
        provider = "anthropic";
        mode = "token";
      };
      "openai-codex:default" = {
        provider = "openai-codex";
        mode = "oauth";
      };
    };
    ".agents.defaults.compaction.mode" = "safeguard";
    ".agents.defaults.compaction.memoryFlush.enabled" = true;
    ".agents.defaults.memorySearch.enabled" = true;
    ".agents.defaults.memorySearch.provider" = "local";
    ".agents.defaults.memorySearch.local.modelPath" = "hf:gpustack/bge-m3-GGUF/bge-m3-Q8_0.gguf";
    ".gateway.port" = openclaw.gatewayPort;
    ".gateway.mode" = "local";
    ".gateway.http.endpoints.chatCompletions.enabled" = true;
  };

  # Telegram patches - per-account so we don't override existing settings
  telegramPatches =
    let
      hasTelegram = telegramAccounts != { };
      # Generate individual account patches
      accountPatches = lib.foldl' (
        acc: name:
        acc
        // {
          ".channels.telegram.accounts.${name}" = telegramAccounts.${name};
        }
      ) { } (lib.attrNames telegramAccounts);
    in
    if hasTelegram then accountPatches // { ".bindings" = telegramBindings; } else { };
in
{
  config = {
    openclaw.configPatches = lib.mkOptionDefault (basePatches // telegramPatches);

    # Secrets: NixOS uses /run/agenix/, standalone Home Manager uses ~/.openclaw/secrets/
    # Generate telegram bot token secret patches for each telegram-enabled agent
    openclaw.secretPatches =
      let
        baseSecrets =
          if isNixOS then
            {
              ".gateway.auth.token" = "/run/agenix/openclaw-gateway-token";
              ".tools.web.search.apiKey" = "/run/agenix/brave-api-key";
            }
          else
            {
              ".gateway.auth.token" = "${homeDir}/.openclaw/secrets/openclaw-gateway-token";
              ".tools.web.search.apiKey" = "${homeDir}/.openclaw/secrets/brave-api-key";
            };

        # Generate bot token secrets for telegram-enabled agents
        telegramSecrets =
          if isNixOS then
            lib.mapAttrs' (name: _: {
              name = ".channels.telegram.accounts.${name}.botToken";
              value = "/run/agenix/telegram-bot-token-${name}";
            }) telegramEnabledAgents
          else
            lib.mapAttrs' (name: _: {
              name = ".channels.telegram.accounts.${name}.botToken";
              value = "${homeDir}/.openclaw/secrets/telegram-bot-token-${name}";
            }) telegramEnabledAgents;
      in
      lib.mkOptionDefault (baseSecrets // telegramSecrets);
  };
}
