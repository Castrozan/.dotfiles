# Declarative patches for openclaw.json.
#
# openclaw.json is app-managed — the gateway, `openclaw configure`, and
# `doctor --fix` all do full JSON overwrites, destroying any inline
# directives. On every nix rebuild, the engine in config-engine.nix applies
# these patches via jq, then writes back atomically. The app can freely
# modify the config between rebuilds; next rebuild re-pins our fields.
#
# Add/remove a pinned field = add/remove one line here.
# Engine details: see config-engine.nix.
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

  # Get agents with discord enabled
  discordEnabledAgents = lib.filterAttrs (_: a: a.discord.enable) openclaw.enabledAgents;

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
      "openai-codex/gpt-5.3-codex"
      "anthropic/claude-sonnet-4-5"
    ];
    ".agents.defaults.models" = {
      "anthropic/claude-opus-4-6" = {
        alias = "opus";
      };
      "anthropic/claude-sonnet-4-5" = {
        alias = "sonnet";
      };
      "openai-codex/gpt-5.3-codex" = {
        alias = "codex";
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
    ".agents.defaults.timeoutSeconds" = 300;
    ".agents.defaults.compaction.mode" = "safeguard";
    ".agents.defaults.compaction.memoryFlush.enabled" = false;
    ".agents.defaults.memorySearch.enabled" = false;
    ".gateway.port" = openclaw.gatewayPort;
    ".gateway.mode" = "local";
    ".gateway.http.endpoints.chatCompletions.enabled" = true;
    ".channels.telegram.commands.nativeSkills" = false;
  };

  # Discord patches - per-account, mirrors telegram pattern
  hasDiscord = discordEnabledAgents != { };

  discordAccounts = lib.mapAttrs (name: agent: {
    name = if agent.telegram.botName != null then agent.telegram.botName else capitalize name;
    enabled = true;
    inherit (agent.discord) dmPolicy groupPolicy;
  }) discordEnabledAgents;

  discordBindings = lib.mapAttrsToList (name: _: {
    agentId = name;
    match = {
      channel = "discord";
      accountId = name;
    };
  }) discordEnabledAgents;

  # Telegram patches - per-account so we don't override existing settings
  telegramPatches =
    let
      hasTelegram = telegramAccounts != { };
      accountPatches = lib.foldl' (
        acc: name:
        acc
        // {
          ".channels.telegram.accounts.${name}" = telegramAccounts.${name};
        }
      ) { } (lib.attrNames telegramAccounts);
    in
    if hasTelegram then accountPatches else { };

  # Discord patches - per-account so we don't override existing settings
  discordPatches =
    let
      accountPatches = lib.foldl' (
        acc: name:
        acc
        // {
          ".channels.discord.accounts.${name}" = discordAccounts.${name};
        }
      ) { } (lib.attrNames discordAccounts);
    in
    if hasDiscord then
      {
        ".channels.discord.enabled" = true;
        ".channels.discord.groupPolicy" = "allowlist";
        ".channels.discord.dmPolicy" = "pairing";
      }
      // accountPatches
    else
      { };

  combinedChannelBindings = telegramBindings ++ discordBindings;
in
{
  config = {
    openclaw.configPatches = lib.mkOptionDefault (
      basePatches // telegramPatches // discordPatches // { ".bindings" = combinedChannelBindings; }
    );

    openclaw.secretPatches =
      let
        agenixSecretsDir = if isNixOS then "/run/agenix" else "${homeDir}/.secrets";

        baseSecrets = {
          ".gateway.auth.token" = "${agenixSecretsDir}/openclaw-gateway-token";
          ".tools.web.search.apiKey" = "${agenixSecretsDir}/brave-api-key";
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

        # Generate bot token secrets for discord-enabled agents
        # Discord uses "token" not "botToken" (botToken is Telegram-only)
        discordSecrets =
          if isNixOS then
            lib.mapAttrs' (name: _: {
              name = ".channels.discord.accounts.${name}.token";
              value = "/run/agenix/discord-bot-token-${name}";
            }) discordEnabledAgents
          else
            lib.mapAttrs' (name: _: {
              name = ".channels.discord.accounts.${name}.token";
              value = "${homeDir}/.openclaw/secrets/discord-bot-token-${name}";
            }) discordEnabledAgents;
      in
      lib.mkOptionDefault (baseSecrets // telegramSecrets // discordSecrets);
  };
}
