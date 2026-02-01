{
  lib,
  config,
  ...
}:
let
  cfg = config.openclaw;
in
{
  options.openclaw = {
    agent = lib.mkOption {
      type = lib.types.str;
      description = "Agent identity name (e.g. cleber, romario)";
    };

    agentEmoji = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Agent emoji identifier";
    };

    agentRole = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Agent role description";
    };

    userName = lib.mkOption {
      type = lib.types.str;
      default = "Lucas";
      description = "Human user's first name";
    };

    workspacePath = lib.mkOption {
      type = lib.types.str;
      default = "openclaw";
      description = "Workspace directory path relative to home";
    };

    gatewayPort = lib.mkOption {
      type = lib.types.port;
      default = 18789;
      description = "Local OpenClaw gateway port";
    };

    model = lib.mkOption {
      type = lib.types.str;
      default = "anthropic/claude-opus-4-5";
      description = "Default model ID for this agent";
    };

    # Computed values derived from config, available for templates
    substitutions = lib.mkOption {
      type = lib.types.listOf (lib.types.listOf lib.types.str);
      internal = true;
      description = "Pair of [placeholders, replacements] for builtins.replaceStrings";
    };
  };

  config.openclaw.substitutions = [
    [
      "@agentName@"
      "@agentEmoji@"
      "@agentRole@"
      "@userName@"
      "@workspacePath@"
      "@gatewayPort@"
      "@model@"
      "@homePath@"
      "@username@"
      "@ttsVoice@"
      "@ttsVoiceAlt@"
      "@ttsEngine@"
    ]
    [
      cfg.agent
      cfg.agentEmoji
      cfg.agentRole
      cfg.userName
      cfg.workspacePath
      (toString cfg.gatewayPort)
      cfg.model
      config.home.homeDirectory
      config.home.username
      cfg.tts.voice
      cfg.tts.voiceAlt
      cfg.tts.engine
    ]
  ];
}
