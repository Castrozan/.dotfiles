{ lib }:
{
  mkWorkspaceProfileLaunchDispatch =
    {
      agentWorkspaceProfiles,
      activationShellStatementsForProfile,
    }:
    let
      profileBranches = lib.concatMapStrings (workspaceProfile: ''
        ${lib.escapeShellArg workspaceProfile.name})
          ${activationShellStatementsForProfile workspaceProfile}
          ;;
      '') agentWorkspaceProfiles.profiles;
    in
    lib.optionalString (agentWorkspaceProfiles.profiles != [ ]) ''
      resolvedWorkspaceProfileName="$(${agentWorkspaceProfiles.resolverExecutable} --working-directory "$PWD" || true)"
      case "$resolvedWorkspaceProfileName" in
        ${profileBranches}
      esac
    '';
}
