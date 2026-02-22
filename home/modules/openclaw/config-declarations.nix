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
  isNixOS, # kept in scope from specialArgs but no longer used here
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
      model =
        lib.optionalAttrs (agent.model.primary != null) { inherit (agent.model) primary; }
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
      "anthropic/claude-opus-4-6"
      "openai-codex/gpt-5.3-codex"
      "nvidia/moonshotai/kimi-k2.5"
    ];
    ".agents.defaults.models" = {
      "anthropic/claude-sonnet-4-6" = {
        alias = "sonnet";
      };
      "anthropic/claude-opus-4-6" = {
        alias = "opus";
      };
      "openai-codex/gpt-5.3-codex" = {
        alias = "codex";
      };
    };
    ".models.mode" = "merge";
    ".models.providers.google.baseUrl" = "https://generativelanguage.googleapis.com/v1beta";
    ".models.providers.google.models" = [ ];
    ".models.providers.nvidia.baseUrl" = "https://integrate.api.nvidia.com/v1";
    ".models.providers.nvidia.api" = "openai-completions";
    ".models.providers.nvidia.models" = [
      {
        id = "moonshotai/kimi-k2.5";
        name = "Kimi K2.5";
      }
    ];
    ".models.providers.openai.baseUrl" = "https://api.openai.com/v1";
    ".models.providers.openai.models" = [ ];
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
    ".agents.defaults.timeoutSeconds" = 600;
    ".agents.defaults.compaction.mode" = "safeguard";
    ".agents.defaults.compaction.memoryFlush.enabled" = true;
    ".agents.defaults.memorySearch.enabled" = true;
    ".agents.defaults.memorySearch.provider" = "openai";
    ".agents.defaults.memorySearch.model" = "text-embedding-3-small";
    ".agents.defaults.memorySearch.fallback" = "gemini";
    ".agents.defaults.memorySearch.sources" = [
      "memory"
      "sessions"
    ];
    ".agents.defaults.memorySearch.experimental.sessionMemory" = true;
    ".agents.defaults.memorySearch.query.maxResults" = 8;
    ".agents.defaults.memorySearch.query.hybrid.enabled" = true;
    ".agents.defaults.memorySearch.query.hybrid.vectorWeight" = 0.7;
    ".agents.defaults.memorySearch.query.hybrid.textWeight" = 0.3;
    ".agents.defaults.memorySearch.cache.enabled" = true;
    ".tools.exec.timeoutSec" = 1800;
    ".tools.exec.notifyOnExit" = true;
    ".gateway.port" = openclaw.gatewayPort;
    ".gateway.mode" = "local";
    ".gateway.reload.mode" = "hybrid";
    ".gateway.http.endpoints.chatCompletions.enabled" = true;
    ".channels.telegram.commands.nativeSkills" = false;
  };

  # Discord patches - per-account, mirrors telegram pattern
  hasDiscord = discordEnabledAgents != { };

  discordAccounts = lib.mapAttrs (name: agent: {
    name = if agent.telegram.botName != null then agent.telegram.botName else capitalize name;
    enabled = true;
    inherit (agent.discord) dmPolicy groupPolicy streamMode;
  }) discordEnabledAgents;

  # Generate per-account voice patches
  discordVoicePatches = lib.foldl' (
    acc: name:
    let
      agent = discordEnabledAgents.${name};
    in
    if agent.discord.voice.enable then
      acc // { ".channels.discord.accounts.${name}.voice.enabled" = true; }
    else
      acc
  ) { } (lib.attrNames discordEnabledAgents);

  # Generate per-account guild patches
  discordGuildPatches = lib.foldl' (
    acc: name:
    let
      agent = discordEnabledAgents.${name};
      guildEntries = lib.mapAttrs' (
        guildId: guildCfg:
        let
          channelEntries = lib.mapAttrs (
            _: chCfg:
            {
              inherit (chCfg) allow;
            }
            // lib.optionalAttrs (chCfg.requireMention != null) { inherit (chCfg) requireMention; }
          ) guildCfg.channels;
          guildValue = {
            inherit (guildCfg) requireMention;
          }
          // lib.optionalAttrs (guildCfg.slug != null) { inherit (guildCfg) slug; }
          // lib.optionalAttrs (guildCfg.channels != { }) { channels = channelEntries; };
        in
        {
          name = ".channels.discord.accounts.${name}.guilds.${guildId}";
          value = guildValue;
        }
      ) agent.discord.guilds;
    in
    acc // guildEntries
  ) { } (lib.attrNames discordEnabledAgents);

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
      // discordVoicePatches
      // discordGuildPatches
    else
      { };

  combinedChannelBindings = telegramBindings ++ discordBindings;
in
{
  config = {
    openclaw.configPatches = lib.mkOptionDefault (
      basePatches // telegramPatches // discordPatches // { ".bindings" = combinedChannelBindings; }
    );

    # All secrets use home-manager agenix paths (~/.secrets/).
    # System-level agenix (/run/agenix/) is not used for openclaw secrets.
    openclaw.secretPatches =
      let
        secretsDir = "${homeDir}/.secrets";

        baseSecrets = {
          ".gateway.auth.token" = "${secretsDir}/openclaw-gateway-token";
          ".tools.web.search.apiKey" = "${secretsDir}/brave-api-key";
          ".agents.defaults.memorySearch.remote.apiKey" = "${secretsDir}/openai-api-key";
          ".models.providers.openai.apiKey" = "${secretsDir}/openai-api-key";
          ".models.providers.google.apiKey" = "${secretsDir}/gemini-api-key";
          ".models.providers.nvidia.apiKey" = "${secretsDir}/nvidia-api-key";
        };

        # Generate bot token secrets for telegram-enabled agents
        telegramSecrets = lib.mapAttrs' (name: _: {
          name = ".channels.telegram.accounts.${name}.botToken";
          value = "${secretsDir}/telegram-bot-token-${name}";
        }) telegramEnabledAgents;

        # Generate bot token secrets for discord-enabled agents
        # Discord uses "token" not "botToken" (botToken is Telegram-only)
        discordSecrets = lib.mapAttrs' (name: _: {
          name = ".channels.discord.accounts.${name}.token";
          value = "${secretsDir}/discord-bot-token-${name}";
        }) discordEnabledAgents;
      in
      lib.mkOptionDefault (baseSecrets // telegramSecrets // discordSecrets);

  };
}
