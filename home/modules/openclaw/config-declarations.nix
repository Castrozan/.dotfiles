{
  config,
  lib,
  ...
}:
let
  inherit (config) openclaw;
  homeDir = config.home.homeDirectory;

  allAgentNames = lib.attrNames openclaw.enabledAgents;

  agentsList = lib.mapAttrsToList (
    name: agent:
    {
      id = name;
      workspace = "${homeDir}/${agent.workspace}";
      model =
        lib.optionalAttrs (agent.model.primary != null) { inherit (agent.model) primary; }
        // lib.optionalAttrs (agent.model.fallbacks != [ ]) { inherit (agent.model) fallbacks; };
      subagents = {
        allowAgents = lib.filter (n: n != name) allAgentNames;
      };
    }
    // lib.optionalAttrs (name == openclaw.defaultAgent) { default = true; }
  ) openclaw.enabledAgents;

  defaultWorkspace =
    if openclaw.defaultAgent != null then
      "${homeDir}/${openclaw.agents.${openclaw.defaultAgent}.workspace}"
    else
      "${homeDir}/openclaw";

  telegramEnabledAgents = lib.filterAttrs (_: a: a.telegram.enable) openclaw.enabledAgents;

  discordEnabledAgents = lib.filterAttrs (_: a: a.discord.enable) openclaw.enabledAgents;

  capitalize = s: lib.toUpper (lib.substring 0 1 s) + lib.substring 1 (-1) s;

  telegramAccounts = lib.mapAttrs (name: agent: {
    name = if agent.telegram.botName != null then agent.telegram.botName else capitalize name;
    enabled = true;
    inherit (agent.telegram) dmPolicy groupPolicy streaming;
  }) telegramEnabledAgents;

  telegramBindings = lib.mapAttrsToList (name: _: {
    agentId = name;
    match = {
      channel = "telegram";
      accountId = name;
    };
  }) telegramEnabledAgents;

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
      "nvidia/meta/llama-3.3-70b-instruct"
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
      {
        id = "deepseek-ai/deepseek-v3.2";
        name = "DeepSeek V3.2";
      }
      {
        id = "meta/llama-3.3-70b-instruct";
        name = "Llama 3.3 70B";
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
    ".session.scope" = "global";
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
    ".tools.agentToAgent.enabled" = true;
    ".tools.agentToAgent.allow" = allAgentNames;
    ".tools.sessions.visibility" = "all";

    ".acp.enabled" = true;
    ".acp.dispatch.enabled" = false;
    ".acp.defaultAgent" = "claude-code";

    ".tools.media.audio.echoTranscript" = true;
    ".tools.media.audio.echoFormat" = "text";

    ".agents.defaults.heartbeat.lightContext" = true;

    ".browser.enabled" = true;
    ".browser.defaultProfile" = "openclaw";
    ".browser.profiles.user" = {
      driver = "existing-session";
      attachOnly = true;
      color = "#4285f4";
    };
    ".browser.profiles.openclaw" = {
      cdpPort = 18800;
      color = "#ea4335";
    };
  };

  hasDiscord = discordEnabledAgents != { };

  discordAccounts = lib.mapAttrs (
    name: agent:
    {
      name = if agent.telegram.botName != null then agent.telegram.botName else capitalize name;
      enabled = true;
      inherit (agent.discord) dmPolicy groupPolicy streaming;
    }
    // lib.optionalAttrs (agent.discord.allowFrom != [ ]) { inherit (agent.discord) allowFrom; }
  ) discordEnabledAgents;

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
    openclaw.configDeletes = [
      ".acp.provenance"
      ".channels.telegram.accounts.clever.streamMode"
      ".channels.telegram.accounts.golden.streamMode"
      ".channels.telegram.accounts.jarvis.streamMode"
      ".channels.discord.accounts.clever.streamMode"
      ".channels.discord.accounts.golden.streamMode"
      ".channels.discord.accounts.jarvis.streamMode"
    ];

    openclaw.configPatches =
      basePatches // telegramPatches // discordPatches // { ".bindings" = combinedChannelBindings; };

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

        telegramSecrets = lib.mapAttrs' (name: _: {
          name = ".channels.telegram.accounts.${name}.botToken";
          value = "${secretsDir}/telegram-bot-token-${name}";
        }) telegramEnabledAgents;

        discordSecrets = lib.mapAttrs' (name: _: {
          name = ".channels.discord.accounts.${name}.token";
          value = "${secretsDir}/discord-bot-token-${name}";
        }) discordEnabledAgents;
      in
      lib.mkOptionDefault (baseSecrets // telegramSecrets // discordSecrets);

  };
}
