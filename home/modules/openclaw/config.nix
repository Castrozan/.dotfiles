{
  lib,
  config,
  ...
}:
let
  inherit (config) openclaw;

  # Agent submodule type
  agentModule = lib.types.submodule {
    options = {
      enable = lib.mkEnableOption "agent";

      isDefault = lib.mkOption {
        type = lib.types.bool;
        default = false;
        description = "Whether this is the default agent for the gateway";
      };

      emoji = lib.mkOption {
        type = lib.types.str;
        default = "";
        description = "Agent emoji identifier";
      };

      role = lib.mkOption {
        type = lib.types.str;
        default = "";
        description = "Agent role description";
      };

      model = lib.mkOption {
        type = lib.types.submodule {
          options = {
            primary = lib.mkOption {
              type = lib.types.str;
              default = "nvidia/moonshotai/kimi-k2.5";
              description = "Primary model ID for this agent";
            };
            fallbacks = lib.mkOption {
              type = lib.types.listOf lib.types.str;
              default = [ ];
              description = "Fallback model IDs";
            };
          };
        };
        default = { };
        description = "Model configuration for this agent";
      };

      workspace = lib.mkOption {
        type = lib.types.str;
        description = "Workspace directory path relative to home";
      };

      skills = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [ ];
        description = "List of skill names to enable for this agent";
      };

      tts = lib.mkOption {
        type = lib.types.submodule {
          options = {
            voice = lib.mkOption {
              type = lib.types.str;
              default = "en-US-GuyNeural";
              description = "Edge-tts voice for this agent";
            };
            engine = lib.mkOption {
              type = lib.types.str;
              default = "edge-tts";
              description = "TTS engine to use";
            };
          };
        };
        default = { };
        description = "TTS configuration for this agent";
      };

      telegram = lib.mkOption {
        type = lib.types.submodule {
          options = {
            enable = lib.mkEnableOption "telegram integration for this agent";
            botName = lib.mkOption {
              type = lib.types.nullOr lib.types.str;
              default = null;
              description = "Display name for the telegram bot (defaults to capitalized agent name)";
            };
            dmPolicy = lib.mkOption {
              type = lib.types.str;
              default = "pairing";
              description = "Direct message policy";
            };
            groupPolicy = lib.mkOption {
              type = lib.types.str;
              default = "allowlist";
              description = "Group message policy";
            };
            streamMode = lib.mkOption {
              type = lib.types.str;
              default = "partial";
              description = "Message streaming mode";
            };
          };
        };
        default = { };
        description = "Telegram bot configuration for this agent";
      };
    };
  };

  # Get enabled agents as attrset
  enabledAgents = lib.filterAttrs (_: a: a.enable) openclaw.agents;

  # Find the default agent (first one marked isDefault, or first enabled)
  defaultAgentName =
    let
      defaultOnes = lib.filterAttrs (_: a: a.isDefault) enabledAgents;
      firstDefault = lib.head (lib.attrNames defaultOnes);
      firstEnabled = lib.head (lib.attrNames enabledAgents);
    in
    if defaultOnes != { } then firstDefault else firstEnabled;
in
{
  options.openclaw = {
    agents = lib.mkOption {
      type = lib.types.attrsOf agentModule;
      default = { };
      description = "Agent configurations";
    };

    userName = lib.mkOption {
      type = lib.types.str;
      default = "Lucas";
      description = "Human user's first name";
    };

    gatewayPort = lib.mkOption {
      type = lib.types.port;
      default = 18789;
      description = "Local OpenClaw gateway port";
    };

    # Derived values (internal)
    enabledAgents = lib.mkOption {
      type = lib.types.attrsOf agentModule;
      internal = true;
      readOnly = true;
      description = "Computed list of enabled agents";
    };

    defaultAgent = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      internal = true;
      readOnly = true;
      description = "Name of the default agent";
    };

    # Internal helper functions
    substituteAgentConfig = lib.mkOption {
      type = lib.types.functionTo (lib.types.functionTo lib.types.str);
      internal = true;
      description = "Reads a file and substitutes @placeholder@ tokens for a specific agent";
    };

    deployToWorkspace = lib.mkOption {
      type = lib.types.functionTo (lib.types.functionTo (lib.types.attrsOf lib.types.anything));
      internal = true;
      description = "Takes an agent name and attrset of {relative-path = value} and deploys to the agent's workspace";
    };

    deployToAllWorkspaces = lib.mkOption {
      type = lib.types.functionTo (lib.types.attrsOf lib.types.anything);
      internal = true;
      description = "Takes an attrset of {relative-path = value} and deploys to all enabled agent workspaces";
    };
  };

  config.openclaw = {
    inherit enabledAgents;
    defaultAgent = defaultAgentName;

    # substituteAgentConfig takes agent name, then file path
    substituteAgentConfig =
      agentName: path:
      let
        agent = openclaw.agents.${agentName};
        homeDir = config.home.homeDirectory;

        # Format skills list for display
        skillsDisplay =
          if agent.skills == [ ] then
            "*(configured via Nix — see skills/ directory)*"
          else
            builtins.concatStringsSep ", " agent.skills;

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
          "@agentSkills@"
        ];
        baseValues = [
          agentName
          agent.emoji
          agent.role
          openclaw.userName
          agent.workspace
          (toString openclaw.gatewayPort)
          agent.model.primary
          homeDir
          config.home.username
          agent.tts.voice
          agent.tts.engine
          skillsDisplay
        ];
        gridNames = builtins.attrNames openclaw.gridPlaceholders;
        gridValues = map (name: openclaw.gridPlaceholders.${name}) gridNames;
        placeholders = basePlaceholders ++ gridNames;
        values = baseValues ++ gridValues;
      in
      builtins.replaceStrings placeholders values (builtins.readFile path);

    # deployToWorkspace takes agent name, then files attrset
    deployToWorkspace =
      agentName: files:
      let
        agent = openclaw.agents.${agentName};
      in
      lib.mapAttrs' (name: value: {
        name = "${agent.workspace}/${name}";
        inherit value;
      }) files;

    # deployToAllWorkspaces deploys same files to all enabled agents
    deployToAllWorkspaces =
      files:
      lib.foldl' (acc: agentName: acc // (openclaw.deployToWorkspace agentName files)) { } (
        lib.attrNames enabledAgents
      );
  };
}
