{
  lib,
  config,
  ...
}:
let
  inherit (config) openclaw;
in
{
  options.openclaw = {
    agent = lib.mkOption {
      type = lib.types.str;
      description = "Agent identity name";
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

    substituteAgentConfig = lib.mkOption {
      type = lib.types.functionTo lib.types.str;
      internal = true;
      description = "Reads a file and substitutes @placeholder@ tokens with agent config values";
    };

    deployToWorkspace = lib.mkOption {
      type = lib.types.functionTo (lib.types.attrsOf lib.types.anything);
      internal = true;
      description = "Takes an attrset of {relative-path = value} and deploys to the workspace";
    };
  };

  config.openclaw = {
    substituteAgentConfig =
      let
        basePlaceholders = [
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
          "@ttsEngine@"
        ];
        baseValues = [
          openclaw.agent
          openclaw.agentEmoji
          openclaw.agentRole
          openclaw.userName
          openclaw.workspacePath
          (toString openclaw.gatewayPort)
          openclaw.model
          config.home.homeDirectory
          config.home.username
          openclaw.tts.voice
          openclaw.tts.engine
        ];
        gridNames = builtins.attrNames openclaw.gridPlaceholders;
        gridValues = map (name: openclaw.gridPlaceholders.${name}) gridNames;
        placeholders = basePlaceholders ++ gridNames;
        values = baseValues ++ gridValues;
      in
      path: builtins.replaceStrings placeholders values (builtins.readFile path);

    deployToWorkspace =
      files:
      lib.mapAttrs' (name: value: {
        name = "${openclaw.workspacePath}/${name}";
        inherit value;
      }) files;
  };
}
