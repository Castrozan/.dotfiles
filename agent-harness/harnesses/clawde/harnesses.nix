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

  claudeSettingsOverlayOfWorkspaceProfile =
    profileName:
    (lib.findFirst (
      workspaceProfile: workspaceProfile.name == profileName
    ) (throw "no workspace profile named ${profileName}") workspaceProfilesCarryingClaudeSettings)
    .claudeCode.settingsOverlay;

  claudeLaunchSettingsOf =
    agent:
    lib.recursiveUpdate
      (lib.optionalAttrs agent.claudeInteractiveSessionSettings (
        config.claude.interactiveSessionSettings or { }
      ))
      (
        lib.optionalAttrs (agent.claudeSettingsWorkspaceProfile != null) (
          claudeSettingsOverlayOfWorkspaceProfile agent.claudeSettingsWorkspaceProfile
        )
      );

  withClaudeLaunchSettings =
    agentName: agent: harnessCommand:
    if agent.claudeLaunchSettings == { } then
      harnessCommand
    else
      let
        inherit (config.clawde.harnesses.claude) binaryInvocation;
        settingsFile = pkgs.writeText "clawde-agent-${agentName}-claude-settings.json" (
          builtins.toJSON agent.claudeLaunchSettings
        );
      in
      lib.replaceStrings [ " ${binaryInvocation} " ] [ " ${binaryInvocation} --settings ${settingsFile} " ]
        harnessCommand;
in
{
  options.clawde.agents = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule (agentModule: {
        options = {
          claudeSettingsWorkspaceProfile = lib.mkOption {
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
              profile on its own. Null adds no overlay; other harnesses ignore it.
            '';
          };

          claudeInteractiveSessionSettings = lib.mkOption {
            type = lib.types.bool;
            default = false;
            description = ''
              Whether this agent launches on the claude harness with the settings the
              plain claude command gives every interactive session, its plugins and
              plugin options, beneath any workspace profile overlay exactly as an
              interactive session layers them. Other harnesses ignore it.
            '';
          };

          claudeLaunchSettings = lib.mkOption {
            type = lib.types.attrsOf lib.types.anything;
            readOnly = true;
            default = claudeLaunchSettingsOf agentModule.config;
            description = ''
              The settings this agent's claude commands receive as one --settings
              file. The agent workspace is often a repository whose committed
              .claude/settings.json clawde must not overwrite, so these travel on the
              command line instead. Empty launches with no --settings flag.
            '';
          };
        };
      })
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
                        "CLAUDE_CODE_EFFORT_LEVEL=${lib.escapeShellArg arguments.agent.reasoningEffort} ${withClaudeLaunchSettings arguments.name arguments.agent (buildCommand arguments)}"
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
