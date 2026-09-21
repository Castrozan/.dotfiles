{
  config,
  lib,
  pkgs,
  ...
}:
let
  interactiveSessionOnlySystemPromptSurfaces = import ./interactive-session-instructions.nix {
    inherit pkgs;
    inherit (config.home) homeDirectory;
  };

  workspaceProfileActivation = import ./workspace-profile-settings-and-instructions.nix {
    inherit pkgs lib interactiveSessionOnlySystemPromptSurfaces;
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
    requiredOrganizationId:
    pkgs.writeShellScriptBin "claude" ''
      ${lib.optionalString (requiredOrganizationId != null) ''
        if [[ "''${1-}" != "auth" ]]; then
          claudeAuthenticationStatus="$(${lib.getExe config.claude.unwrappedPackage} auth status --json 2>/dev/null)" || claudeAuthenticationStatus=""
          authenticatedOrganizationId="$(printf '%s' "$claudeAuthenticationStatus" | ${lib.getExe pkgs.jq} --exit-status --raw-output 'select(.loggedIn == true) | .orgId // empty' 2>/dev/null)" || authenticatedOrganizationId=""
          if [[ "$authenticatedOrganizationId" != ${lib.escapeShellArg requiredOrganizationId} ]]; then
            printf 'Claude is not authenticated to the required Claude organization on this machine; run `claude auth login` and select it.\n' >&2
            exit 1
          fi
        fi
      ''}
      claudeSystemPromptFile="${interactiveSessionOnlySystemPromptSurfaces}"
      workspaceProfileArguments=()
      resolvedWorkspaceProfileName=""
      ${workspaceProfileLaunchDispatch}
      export AGENT_INTERACTIVE_PREFERENCES_PATH="$claudeSystemPromptFile"
      exec ${lib.getExe config.claude.unwrappedPackage} \
        --append-system-prompt-file "$claudeSystemPromptFile" \
        "''${workspaceProfileArguments[@]}" \
        "$@"
    '';

  unrestrictedClaudeInteractivePackage = makeClaudeInteractivePackage null;
  claudePackage = makeClaudeInteractivePackage config.claude.requiredOrganizationId;
in
{
  options.claude = {
    package = lib.mkOption {
      type = lib.types.package;
      default = claudePackage;
      readOnly = true;
      description = "The package exposed as the plain claude command, carrying the interactive prompt, workspace profile, and any required organization admission policy.";
    };

    unrestrictedInteractivePackage = lib.mkOption {
      type = lib.types.package;
      default = unrestrictedClaudeInteractivePackage;
      readOnly = true;
      description = "The interactive Claude package with workspace-profile activation but without the plain command's organization admission policy. Alternate model-provider frontends consume this capability.";
    };

    requiredOrganizationId = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = "The exact organization ID that must own the authenticated Claude account before the plain command may start. Null disables organization admission.";
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
