{ lib }:
let
  shellPathExpression =
    path:
    if lib.hasPrefix "~/" path then
      ''"$HOME"/${lib.escapeShellArg (lib.removePrefix "~/" path)}''
    else
      lib.escapeShellArg path;

  sessionEnvironmentExportStatementsForProfile =
    workspaceProfile:
    lib.concatStrings (
      lib.mapAttrsToList (variableName: value: ''
        export ${variableName}=${lib.escapeShellArg value}
      '') workspaceProfile.sessionEnvironment
      ++ lib.mapAttrsToList (variableName: secretFile: ''
        if [ -r ${shellPathExpression secretFile} ]; then
          export ${variableName}="$(<${shellPathExpression secretFile})"
        fi
      '') workspaceProfile.sessionEnvironmentFromFiles
    );
in
{
  mkWorkspaceProfileLaunchDispatch =
    {
      agentWorkspaceProfiles,
      activationShellStatementsForProfile,
    }:
    let
      profileBranches = lib.concatMapStrings (workspaceProfile: ''
        ${lib.escapeShellArg workspaceProfile.name})
          ${sessionEnvironmentExportStatementsForProfile workspaceProfile}
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
