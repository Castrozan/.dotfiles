{
  config,
  lib,
  pkgs,
  hostname,
  ...
}:
{
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
                        "CLAUDE_CODE_EFFORT_LEVEL=${lib.escapeShellArg arguments.agent.reasoningEffort} ${buildCommand arguments}"
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
