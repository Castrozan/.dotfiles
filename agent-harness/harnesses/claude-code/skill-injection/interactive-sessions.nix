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

  requiredWorkspaceProfileName = config.claude.requiredWorkspaceProfileName;

  # No servant wiring here on purpose. The Servant is derived at SessionStart from
  # the id Claude Code mints for itself, so this wrapper neither knows nor needs to
  # know which one a launch draws, and a resume lands on the same one for free.
  claudeInteractiveScript = pkgs.writeShellScriptBin "claude" ''
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
in
{
  options.claude = {
    package = lib.mkOption {
      type = lib.types.package;
      default = claudeInteractiveScript;
      readOnly = true;
      description = "The claude every keyboard-driven launch resolves, wrapping the unwrapped package with the human's own reply-shape system prompt and the resolved workspace profile. It carries the plain `claude` name so a herdr agent, a script or a launcher gets the same surface the human's shell does.";
    };

    requiredWorkspaceProfileName = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = "The workspace profile that must match the launch directory before interactive Claude may start. Null permits every directory.";
    };
  };

  config.home = {
    packages = [ claudeInteractiveScript ];
    file.".local/bin/claude" = {
      source = "${claudeInteractiveScript}/bin/claude";
      force = true;
    };
  };
}
