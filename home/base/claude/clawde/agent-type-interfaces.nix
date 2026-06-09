{ lib, ... }:
{
  options.clawde.agentTypes = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        options = {
          runtimeInstructions = lib.mkOption {
            type = lib.types.lines;
            default = "";
            description = "Markdown role block concatenated into the agent CLAUDE.md after the base clawde-runtime block when an agent picks this type. The role analog of channelAdapters.instructions.";
          };
          personalityTemplateFor = lib.mkOption {
            type = lib.types.functionTo (lib.types.nullOr lib.types.lines);
            default = _: null;
            description = "Function: agent -> personality text with typeParams substituted, or null to leave personality to the instance.";
          };
          defaultModel = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Model alias inherited by agents of this type unless the instance overrides it. Null inherits nothing.";
          };
          defaultPermissionMode = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Permission mode inherited unless the instance overrides it.";
          };
          defaultHeartbeatInterval = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Heartbeat cron expression inherited unless the instance overrides it.";
          };
          defaultHeartbeatPrompt = lib.mkOption {
            type = lib.types.nullOr lib.types.lines;
            default = null;
            description = "Heartbeat tick prompt inherited unless the instance overrides it.";
          };
          defaultHeartbeatGateCommand = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Heartbeat gate command inherited unless the instance overrides it.";
          };
          defaultActiveHoursStart = lib.mkOption {
            type = lib.types.nullOr lib.types.int;
            default = null;
            description = "Active-hours start inherited unless the instance overrides it.";
          };
          defaultActiveHoursEnd = lib.mkOption {
            type = lib.types.nullOr lib.types.int;
            default = null;
            description = "Active-hours end inherited unless the instance overrides it.";
          };
          defaultDailySessionRotation = lib.mkOption {
            type = lib.types.nullOr lib.types.bool;
            default = null;
            description = "Daily session rotation inherited unless the instance overrides it.";
          };
          defaultDenyToolPatterns = lib.mkOption {
            type = lib.types.listOf lib.types.str;
            default = [ ];
            description = "Deny tool patterns added to every agent of this type. Composes additively with the instance's own denyToolPatterns.";
          };
          defaultSkillDirectories = lib.mkOption {
            type = lib.types.listOf lib.types.str;
            default = [ ];
            description = "Skill directories added to every agent of this type. Composes additively with the instance's own skillDirectories.";
          };
          workspaceDirectoryFor = lib.mkOption {
            type = lib.types.functionTo (lib.types.nullOr lib.types.str);
            default = _: null;
            description = "Function: agent -> absolute workspace path, or null to fall back to the channel adapter / clawde default.";
          };
          agentActivationScriptFor = lib.mkOption {
            type = lib.types.functionTo lib.types.str;
            default = _: "";
            description = "Function: { name, agent, workspaceDirectory, claudeBinary } -> shell snippet appended to home.activation for type-specific workspace seeding.";
          };
          preActivation = lib.mkOption {
            type = lib.types.nullOr lib.types.str;
            default = null;
            description = "Optional activation snippet run once when at least one agent uses this type.";
          };
          packages = lib.mkOption {
            type = lib.types.listOf lib.types.package;
            default = [ ];
            description = "Packages added to home.packages only when at least one agent of this type is declared on the host.";
          };
          requiredParams = lib.mkOption {
            type = lib.types.listOf lib.types.str;
            default = [ ];
            description = "typeParams.<type> field names that must be set and non-null on every agent of this type. Enforced as a build-time assertion.";
          };
        };
      }
    );
    default = { };
    description = "Agent type implementations. Each module that wants to provide a new agent.type registers itself here.";
  };
}
