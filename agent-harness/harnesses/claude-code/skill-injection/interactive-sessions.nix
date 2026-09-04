{
  config,
  lib,
  pkgs,
  ...
}:
let
  interactiveSessionSystemPromptText = lib.concatStringsSep "\n" [
    (builtins.readFile ../../../../agent-harness/agent-instructions/skills/humanize/references/interactive-communication.md)
    (builtins.readFile ../../../../agent-harness/agent-instructions/core-rules/adaptive-implementation-delivery-process.md)
    (builtins.readFile ../../../../agent-harness/agent-instructions/core-rules/servant-identity.md)
  ];

  interactiveSessionOnlySystemPromptSurfaces = pkgs.writeText "claude-interactive-session-only-system-prompt-surfaces.md" interactiveSessionSystemPromptText;

  workspaceProfileActivation = import ../workspace-profile-activation.nix {
    inherit pkgs lib interactiveSessionSystemPromptText;
  };

  inherit (import ../../../workspace-profiles/activation/harness-launch-dispatch.nix { inherit lib; })
    mkWorkspaceProfileLaunchDispatch
    ;

  workspaceProfileLaunchDispatch = mkWorkspaceProfileLaunchDispatch {
    inherit (config) agentWorkspaceProfiles;
    inherit (workspaceProfileActivation) activationShellStatementsForProfile;
  };

  # No servant wiring here on purpose. The Servant is derived at SessionStart from
  # the id Claude Code mints for itself, so this wrapper neither knows nor needs to
  # know which one a launch draws, and a resume lands on the same one for free.
  makeClaudeInteractivePackage =
    requiredWorkspaceProfileName:
    pkgs.writeShellScriptBin "claude" ''
      claudeSystemPromptFile="${interactiveSessionOnlySystemPromptSurfaces}"
      workspaceProfileArguments=()
      resolvedWorkspaceProfileName=""
      ${lib.optionalString (requiredWorkspaceProfileName != null) ''
        unset AGENT_WORKSPACE_PROFILE AGENT_WORKSPACE_PROFILE_ROUTING_TABLE
      ''}
      ${workspaceProfileLaunchDispatch}
      ${lib.optionalString (requiredWorkspaceProfileName != null) ''
        if [[ "$resolvedWorkspaceProfileName" != ${lib.escapeShellArg requiredWorkspaceProfileName} ]]; then
          printf 'Claude is restricted to the %s workspace profile on this machine; %s is outside it.\n' ${lib.escapeShellArg requiredWorkspaceProfileName} "$PWD" >&2
          exit 1
        fi
      ''}
      export AGENT_INTERACTIVE_PREFERENCES_PATH="$claudeSystemPromptFile"
      exec ${lib.getExe config.claude.unwrappedPackage} \
        --append-system-prompt-file "$claudeSystemPromptFile" \
        "''${workspaceProfileArguments[@]}" \
        "$@"
    '';

  unrestrictedClaudeInteractivePackage = makeClaudeInteractivePackage null;
  claudePackage = makeClaudeInteractivePackage config.claude.requiredWorkspaceProfileName;
in
{
  options.claude = {
    package = lib.mkOption {
      type = lib.types.package;
      default = claudePackage;
      readOnly = true;
      description = "The package exposed as the plain claude command, carrying the interactive prompt, workspace profile, and any required workspace-profile admission policy.";
    };

    unrestrictedInteractivePackage = lib.mkOption {
      type = lib.types.package;
      default = unrestrictedClaudeInteractivePackage;
      readOnly = true;
      description = "The interactive Claude package with workspace-profile activation but without the plain command's admission policy. Alternate model-provider frontends consume this capability.";
    };

    requiredWorkspaceProfileName = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = "The workspace profile that must match the launch directory before interactive Claude may start. Null permits every directory.";
    };
  };

  config.home = {
    packages = [ claudePackage ];
    file.".local/bin/claude" = {
      source = "${claudePackage}/bin/claude";
      force = true;
    };
  };
}
