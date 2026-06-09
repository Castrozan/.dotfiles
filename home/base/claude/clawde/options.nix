{
  lib,
  ...
}:
{
  options.clawde.agents = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        options = {
          personality = lib.mkOption {
            type = lib.types.nullOr lib.types.lines;
            default = null;
            description = "Identity, role, personality - the specialization-layer content unique to this agent. Null inherits the agent type's personality template; the effective value must be non-null.";
          };
          additionalInstructions = lib.mkOption {
            type = lib.types.lines;
            default = "";
            description = "Extra instructions concatenated after base + channel adapter blocks. Overlays for further specialization (PM, browser, etc).";
          };
          model = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Claude model alias (opus, sonnet, haiku). Null inherits the agent type's default, falling back to sonnet.";
          };
          skillDirectories = lib.mkOption {
            type = lib.types.listOf lib.types.str;
            default = [ ];
            description = "Absolute paths passed as --add-dir. Composed additively with the agent type's default skill directories.";
          };
          denyToolPatterns = lib.mkOption {
            type = lib.types.listOf lib.types.str;
            default = [ ];
            description = "Tool patterns written into the agent workspace .claude/settings.json under permissions.deny. Composed additively with the agent type's default deny patterns.";
          };
          permissionMode = lib.mkOption {
            type = lib.types.nullOr (
              lib.types.enum [
                "default"
                "acceptEdits"
                "plan"
                "bypassPermissions"
              ]
            );
            default = null;
            description = "Claude Code permission mode. Null inherits the agent type's default, falling back to 'default'. 'bypassPermissions' for fully autonomous agents.";
          };
          heartbeatInterval = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Cron expression. When set, the agent runs an autonomous polling loop. Null inherits the agent type's default.";
          };
          heartbeatPrompt = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Prompt sent on each heartbeat tick. Required when the effective heartbeatInterval is set. Null inherits the agent type's default.";
          };
          heartbeatGateCommand = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Shell command run before each heartbeat tick. Exit 0 fires the tick and wakes the LLM; any non-zero exit skips the tick without spending tokens. Null inherits the agent type's default, then always fires. Only meaningful when heartbeatInterval is set.";
          };
          activeHoursStart = lib.mkOption {
            type = lib.types.nullOr lib.types.int;
            default = null;
            description = "Hour (0-23) when agent becomes active. Null inherits the agent type's default, then 24/7.";
          };
          activeHoursEnd = lib.mkOption {
            type = lib.types.nullOr lib.types.int;
            default = null;
            description = "Hour (0-23) when agent goes dormant. Null inherits the agent type's default.";
          };
          dailySessionRotation = lib.mkOption {
            type = lib.types.nullOr lib.types.bool;
            default = null;
            description = "Kill and restart the Claude process once per day to prevent context accumulation. Null inherits the agent type's default, then false.";
          };
          expose = lib.mkOption {
            type = lib.types.submodule {
              options = {
                a2a = lib.mkOption {
                  type = lib.types.submodule {
                    options = {
                      enable = lib.mkOption {
                        type = lib.types.bool;
                        default = false;
                        description = "Expose this agent as an A2A peer over HTTP. Spawns a sibling tmux window running the a2a-server wrapping this agent.";
                      };
                      listenHost = lib.mkOption {
                        type = lib.types.str;
                        default = "127.0.0.1";
                        description = "Bind host for the A2A HTTP server. The transport has zero built-in auth; binding to 0.0.0.0 exposes the agent to anyone who can reach the LAN. Front any non-loopback bind with a reverse proxy that adds authentication.";
                      };
                      listenPort = lib.mkOption {
                        type = lib.types.int;
                        default = 7001;
                        description = "Bind port for the A2A HTTP server. Must be unique across all clawde agents.";
                      };
                      publicEndpointUrl = lib.mkOption {
                        type = lib.types.nullOr lib.types.str;
                        default = null;
                        description = "URL advertised in the Agent Card. Null derives http://<listenHost>:<listenPort>.";
                      };
                      agentDescriptionForCard = lib.mkOption {
                        type = lib.types.str;
                        default = "";
                        description = "Free-form description published in the Agent Card. Defaults to the agent name when empty.";
                      };
                      tmuxMeaningfulLinePattern = lib.mkOption {
                        type = lib.types.str;
                        default = "^⏺ ";
                        description = "Regex matching the only pane lines that count as meaningful new output. Filters out status-line and spinner redraws so the a2a-server's idle auto-complete fires. Default '^⏺ ' matches claude-code response markers.";
                      };
                    };
                  };
                  default = { };
                  description = "A2A peer exposure configuration.";
                };
              };
            };
            default = { };
            description = "Interop adapters that expose this agent to non-channel consumers (other agents, scripts, services).";
          };

          workspaceDirectory = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Override the agent's workspace path. When null, the agent type then the active channel adapter decides (and falls back to ~/clawde/<name>).";
          };

          tmuxSession = lib.mkOption {
            type = lib.types.str;
            default = "clawde";
            description = "tmux session name that hosts this agent's window. Agents sharing the same value live as windows of the same tmux session; distinct values create separate sessions, all supervised by the single clawde systemd service. Defaults to 'clawde'.";
          };

          channel = lib.mkOption {
            type = lib.types.submodule {
              options.type = lib.mkOption {
                type = lib.types.str;
                default = "none";
                description = "Channel adapter type. 'none' means the agent has no inbound channel and is invoked manually. Any other value must match a registered clawde.channelAdapters entry. Adapters extend this submodule with their own option subkey (e.g., channel.discord, channel.pm).";
              };
            };
            default = { };
            description = "Channel adapter configuration (how the agent receives and sends messages).";
          };

          type = lib.mkOption {
            type = lib.types.str;
            default = "generic";
            description = "Agent type. Selects a registered clawde.agentTypes entry whose defaults (model, heartbeat, personality template, deny patterns, skill directories, packages) are inherited by this agent unless the instance overrides them. 'generic' inherits nothing.";
          };

          typeParams = lib.mkOption {
            type = lib.types.submodule { options = { }; };
            default = { };
            description = "Per-agent parameters consumed by the agent's type. Each agent type re-opens this submodule with its own subkey (e.g., typeParams.project-manager).";
          };
        };
      }
    );
    default = { };
    description = "clawde persistent agents - each becomes a window in the clawde tmux session.";
  };
}
