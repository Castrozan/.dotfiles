{ config, lib, ... }:
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
                _:
                lib.mkOption {
                  apply =
                    buildCommand:
                    if name != "claude" || buildCommand == null then
                      buildCommand
                    else
                      arguments:
                      "CLAUDE_CODE_EFFORT_LEVEL=${lib.escapeShellArg arguments.agent.reasoningEffort} ${buildCommand arguments}";
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
