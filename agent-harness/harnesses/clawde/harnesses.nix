{
  config,
  lib,
  pkgs,
  hostname,
  ...
}:
let
  workspaceProfilesCarryingClaudeSettings = lib.filter (
    workspaceProfile: workspaceProfile.claudeCode ? settingsOverlay
  ) (config.agentWorkspaceProfiles.profiles or [ ]);

  workspaceProfileSettingsFile = import ../claude-code/settings/workspace-profile-settings-json.nix {
    inherit pkgs;
  };

  claudeSettingsFileOfWorkspaceProfile =
    profileName:
    workspaceProfileSettingsFile (
      lib.findFirst (
        workspaceProfile: workspaceProfile.name == profileName
      ) (throw "no workspace profile named ${profileName}") workspaceProfilesCarryingClaudeSettings
    );

  withWorkspaceProfileClaudeSettings =
    agent: harnessCommand:
    if agent.claudeSettingsWorkspaceProfile == null then
      harnessCommand
    else
      let
        inherit (config.clawde.harnesses.claude) binaryInvocation;
        settingsFlag = "--settings ${claudeSettingsFileOfWorkspaceProfile agent.claudeSettingsWorkspaceProfile}";
      in
      lib.replaceStrings [ " ${binaryInvocation} " ] [ " ${binaryInvocation} ${settingsFlag} " ]
        harnessCommand;
in
{
  options.clawde.agents = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        options.claudeSettingsWorkspaceProfile = lib.mkOption {
          type = lib.types.nullOr (
            lib.types.enum (
              map (workspaceProfile: workspaceProfile.name) workspaceProfilesCarryingClaudeSettings
            )
          );
          default = null;
          description = ''
            Workspace profile whose Claude Code settings overlay this agent launches
            with on the claude harness, so it loads the same plugins, plugin options
            and marketplaces an interactive session in that workspace gets. Clawde
            runs the unwrapped claude binary, which never resolves a workspace
            profile on its own, and the agent workspace is often a repository whose
            committed .claude/settings.json clawde must not overwrite, so the
            overlay travels as a --settings file instead. Null launches with no
            overlay; other harnesses ignore it.
          '';
        };
      }
    );
  };

  options.clawde.harnesses = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule (
        { name, ... }:
        {
          options =
            lib.genAttrs
              [
                "buildLaunchCommandFor"
                "buildRunOnceCommandFor"
                "buildOneShotTurnCommandFor"
              ]
              (
                commandBuilderName:
                lib.mkOption {
                  apply =
                    buildCommand:
                    if buildCommand == null then
                      buildCommand
                    else
                      arguments:
                      if name == "claude" then
                        "CLAUDE_CODE_EFFORT_LEVEL=${lib.escapeShellArg arguments.agent.reasoningEffort} ${withWorkspaceProfileClaudeSettings arguments.agent (buildCommand arguments)}"
                      else if
                        name == "codex"
                        && hostname == "rin"
                        && arguments.name == "steward"
                        && commandBuilderName == "buildLaunchCommandFor"
                      then
                        "${pkgs.python312}/bin/python3 ${./scripts/steward_terminal_space.py} && ${buildCommand arguments}"
                      else
                        buildCommand arguments;
                }
              );
        }
      )
    );
  };

  config = {
    clawde.harnesses =
      lib.optionalAttrs (config ? claude) {
        claude.package = config.claude.unwrappedPackage;
      }
      // lib.optionalAttrs (config ? codex) {
        codex.package = config.codex.unwrappedPackage;
      }
      // lib.optionalAttrs (config ? opencode) {
        opencode.package = config.opencode.unwrappedPackage;
      };

    home.file =
      lib.mkIf
        (
          config ? codex
          && lib.any (agent: agent.harness == "codex") (builtins.attrValues config.clawde.agents)
        )
        {
          "clawde/harness-home/codex/bin/codex-code-mode-host".source =
            "${config.clawde.harnesses.codex.package}/bin/codex-code-mode-host";
        };
  };
}
