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
              default = "anthropic/claude-opus-4-6";
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
            openaiVoice = lib.mkOption {
              type = lib.types.str;
              default = "onyx";
              description = "OpenAI TTS voice for voice-pipeline";
            };
          };
        };
        default = { };
        description = "TTS configuration for this agent";
      };

      telegram = lib.mkOption {
        type = lib.types.submodule {
          options = {
            enable = lib.mkEnableOption "telegram polling for this agent (only one machine may poll a given bot token)";
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
              default = "off";
              description = "Message streaming mode";
            };
          };
        };
        default = { };
        description = "Telegram bot configuration for this agent";
      };

      discord = lib.mkOption {
        type = lib.types.submodule {
          options = {
            enable = lib.mkEnableOption "discord bot for this agent (token stored via agenix)";
            dmPolicy = lib.mkOption {
              type = lib.types.str;
              default = "pairing";
              description = "Direct message policy";
            };
            groupPolicy = lib.mkOption {
              type = lib.types.str;
              default = "allowlist";
              description = "Guild message policy";
            };
          };
        };
        default = { };
        description = "Discord bot configuration for this agent";
      };
    };
  };

  # Get enabled agents as attrset
  enabledAgents = lib.filterAttrs (_: a: a.enable) openclaw.agents;

  # Find the default agent (first one marked isDefault, or first enabled)
  defaultAgentName =
    let
      defaultOnes = lib.filterAttrs (_: a: a.isDefault) enabledAgents;
      defaultNames = lib.attrNames defaultOnes;
      enabledNames = lib.attrNames enabledAgents;
    in
    if defaultNames != [ ] then
      lib.head defaultNames
    else if enabledNames != [ ] then
      lib.head enabledNames
    else
      null;
in
{
  options.openclaw = {
    defaults = lib.mkOption {
      type = lib.types.submodule {
        options.model = lib.mkOption {
          type = lib.types.submodule {
            options = {
              primary = lib.mkOption {
                type = lib.types.str;
                default = "anthropic/claude-opus-4-6";
              };
              heartbeat = lib.mkOption {
                type = lib.types.str;
                default = "openai-codex/gpt-5.3-codex";
              };
              subagents = lib.mkOption {
                type = lib.types.str;
                default = "anthropic/claude-opus-4-6";
              };
            };
          };
          default = { };
        };
      };
      default = { };
    };

    agents = lib.mkOption {
      type = lib.types.attrsOf agentModule;
      default = { };
      description = "Agent configurations. Each agent must be declared on exactly one machine — Telegram bot tokens support only one polling instance. Use memorySync to share agent memory across machines without duplicating declarations.";
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

    notifyTopic = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "ntfy.sh topic ID for push notifications";
    };

    coreRulesContent = lib.mkOption {
      type = lib.types.lines;
      default = "";
      description = "Content for @CORE_RULES@ placeholder in template substitution";
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

    deployDir = lib.mkOption {
      type = lib.types.functionTo (lib.types.attrsOf lib.types.anything);
      internal = true;
      description = ''
        Deploy files from a directory to all enabled agent workspaces.
        Returns home.file attrset. Options:
          src        - source directory path (required)
          prefix     - path prefix in workspace (e.g. "rules")
          filter     - function (name -> type -> bool) to filter entries
          exclude    - list of filenames to skip
          executable - set executable bit on deployed files
          force      - force overwrite existing files
          substitute - apply @placeholder@ template substitution (default true)
          recurse    - treat src entries as directories, collect files from each
      '';
    };

    deployGenerated = lib.mkOption {
      type = lib.types.functionTo (lib.types.attrsOf lib.types.anything);
      internal = true;
      description = "Deploy programmatically generated files. Takes (agentName -> agent -> files attrset) function.";
    };

    gridPlaceholders = lib.mkOption {
      type = lib.types.attrsOf lib.types.str;
      default = { };
      internal = true;
      description = "Grid-derived placeholder values for substituteAgentConfig";
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
          "@notifyTopic@"
          "@CORE_RULES@"
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
          openclaw.notifyTopic
          openclaw.coreRulesContent
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

    # deployDir: read files from a directory, substitute, deploy to all agents
    deployDir =
      {
        src,
        prefix ? "",
        filter ? (_: _: true),
        filterForAgent ? (
          _: _: _:
          true
        ),
        exclude ? [ ],
        executable ? false,
        force ? false,
        substitute ? true,
        recurse ? false,
      }:
      let
        entries = builtins.readDir src;
        pfx = if prefix == "" then "" else "${prefix}/";

        mkFileEntry =
          agentName: filePath:
          (
            if substitute then
              { text = openclaw.substituteAgentConfig agentName filePath; }
            else
              { source = filePath; }
          )
          // lib.optionalAttrs executable { executable = true; }
          // lib.optionalAttrs force { force = true; };

        # Collect files from a directory, recursing one level into subdirectories
        collectDirFiles =
          agentName: basePath: dirPrefix:
          let
            dirEntries = builtins.readDir basePath;
            names = builtins.attrNames dirEntries;
            regularFiles = builtins.filter (n: dirEntries.${n} == "regular") names;
            subDirs = builtins.filter (n: dirEntries.${n} == "directory") names;
          in
          (map (f: {
            name = "${dirPrefix}${f}";
            value = mkFileEntry agentName (basePath + "/${f}");
          }) regularFiles)
          ++ builtins.concatMap (
            d:
            let
              subPath = basePath + "/${d}";
              subEntries = builtins.readDir subPath;
              subFiles = builtins.filter (n: subEntries.${n} == "regular") (builtins.attrNames subEntries);
            in
            map (f: {
              name = "${dirPrefix}${d}/${f}";
              value = mkFileEntry agentName (subPath + "/${f}");
            }) subFiles
          ) subDirs;

        mkAgentFiles =
          agentName:
          if recurse then
            # Recurse mode: each qualifying entry in src is a directory to process
            let
              dirs = builtins.filter (
                n:
                entries.${n} == "directory"
                && !builtins.elem n exclude
                && filter n "directory"
                && filterForAgent agentName n "directory"
              ) (builtins.attrNames entries);
            in
            builtins.listToAttrs (
              builtins.concatMap (d: collectDirFiles agentName (src + "/${d}") "${pfx}${d}/") dirs
            )
          else
            # Flat mode: process regular files in src directly
            let
              files = builtins.filter (
                n:
                entries.${n} == "regular"
                && !builtins.elem n exclude
                && filter n "regular"
                && filterForAgent agentName n "regular"
              ) (builtins.attrNames entries);
            in
            builtins.listToAttrs (
              map (f: {
                name = "${pfx}${f}";
                value = mkFileEntry agentName (src + "/${f}");
              }) files
            );
      in
      lib.foldl' (
        acc: agentName: acc // (openclaw.deployToWorkspace agentName (mkAgentFiles agentName))
      ) { } (lib.attrNames enabledAgents);

    # deployGenerated: deploy programmatically generated files to all agents
    deployGenerated =
      mkFiles:
      lib.foldl' (
        acc: agentName:
        let
          agent = openclaw.agents.${agentName};
        in
        acc // (openclaw.deployToWorkspace agentName (mkFiles agentName agent))
      ) { } (lib.attrNames enabledAgents);
  };
}
