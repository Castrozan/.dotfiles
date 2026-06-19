{ lib, ... }:
{
  options.clawde.channelAdapters = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        options = {
          instructions = lib.mkOption {
            type = lib.types.lines;
            default = "";
            description = "Markdown block concatenated into the agent CLAUDE.md after the base clawde-runtime block when an agent picks this channel.type.";
          };
          launchFlags = lib.mkOption {
            type = lib.types.functionTo lib.types.str;
            default = _: "";
            description = "Function: agent -> shell string of extra flags appended to the claude command line.";
          };
          environmentSetterFor = lib.mkOption {
            type = lib.types.functionTo lib.types.str;
            default = _: "";
            description = "Function: { name, agent } -> shell prefix that exports any env vars the adapter needs in the agent's launch command (e.g., DISCORD_BOT_TOKEN=$(cat ...), DISCORD_STATE_DIR=...).";
          };
          workspaceDirectoryFor = lib.mkOption {
            type = lib.types.functionTo (lib.types.nullOr lib.types.str);
            default = _: null;
            description = "Function: agent -> absolute workspace path, or null to fall back to the clawde default (~/clawde/<name>).";
          };
          agentActivationScriptFor = lib.mkOption {
            type = lib.types.functionTo lib.types.str;
            default = _: "";
            description = "Function: { name, agent, workspaceDirectory, claudeBinary } -> shell snippet appended to home.activation. Used for adapter-specific workspace seeding (HEARTBEAT.md path, .claude.json placement, etc).";
          };
          preActivation = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Optional activation snippet run once when at least one agent uses this adapter (e.g., marketplace pull, plugin install).";
          };
        };
      }
    );
    default = { };
    description = "Channel adapter implementations. Each module that wants to provide a new agent.channel.type registers itself here.";
  };
}
