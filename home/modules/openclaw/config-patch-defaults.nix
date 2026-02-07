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
    ".agents.list" = agentsList;
    ".agents.defaults.workspace" = defaultWorkspace;
    ".agents.defaults.model.primary" = "openai-codex/gpt-5.3-codex";
    ".agents.defaults.heartbeat.model" = "nvidia/moonshotai/kimi-k2.5";
    ".agents.defaults.subagents.model" = "openai-codex/gpt-5.2-codex";
    ".agents.defaults.model.fallbacks" = [
      "nvidia/moonshotai/kimi-k2.5"
      "openai-codex/gpt-5.3-codex"
      "anthropic/claude-sonnet-4-5"
      "anthropic/claude-opus-4-5"
    ];
    ".agents.defaults.models" = {
      "anthropic/claude-opus-4-5" = {
        alias = "opus";
      };
      "anthropic/claude-sonnet-4-5" = {
        alias = "sonnet";
      };
      "nvidia/moonshotai/kimi-k2.5" = {
        alias = "kimi";
      };
    };
    ".models.mode" = "merge";
    ".models.providers.nvidia" = {
      baseUrl = "https://integrate.api.nvidia.com/v1";
      api = "openai-completions";
      models = [
        {
          id = "moonshotai/kimi-k2.5";
          name = "Kimi K2.5 (NVIDIA NIM)";
        }
      ];
    };
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
    ".gateway.port" = openclaw.gatewayPort;
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
              ".models.providers.nvidia.apiKey" = "/run/agenix/nvidia-api-key";
            }
          else
            {
              ".gateway.auth.token" = "${homeDir}/.openclaw/secrets/openclaw-gateway-token";
              ".tools.web.search.apiKey" = "${homeDir}/.openclaw/secrets/brave-api-key";
              ".models.providers.nvidia.apiKey" = "${homeDir}/.openclaw/secrets/nvidia-api-key";
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
