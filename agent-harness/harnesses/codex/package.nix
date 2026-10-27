{
  pkgs,
  lib,
  config,
  latest,
  inputs,
  ...
}:
let
  codex-unwrapped = import ./unwrapped-package.nix {
    inherit
      pkgs
      lib
      latest
      inputs
      ;
  };

  interactivePreferencesFile = import ./interactive-instructions.nix {
    inherit pkgs;
    inherit (config.home) homeDirectory;
  };

  workspaceProfileActivation = import ./workspace-profile-activation.nix {
    inherit pkgs lib interactivePreferencesFile;
  };

  inherit (import ../../workspace-profiles/activation/harness-launch-dispatch.nix { inherit lib; })
    mkWorkspaceProfileLaunchDispatch
    ;

  workspaceProfileLaunchDispatch = mkWorkspaceProfileLaunchDispatch {
    inherit (config) agentWorkspaceProfiles;
    inherit (workspaceProfileActivation) activationShellStatementsForProfile;
  };

  workspaceProfileLaunchDispatchFile = pkgs.writeText "codex-workspace-profile-launch-dispatch" workspaceProfileLaunchDispatch;

  hookTrustExecutable = pkgs.writeShellScript "codex-approve-discovered-hooks" ''
    exec ${pkgs.python312}/bin/python3 ${./scripts/hook_trust}/approve.py "$@"
  '';

  sessionPython = pkgs.python312.withPackages (pythonPackages: [
    pythonPackages.tomlkit
    pythonPackages.websockets
  ]);

  sessionScripts = pkgs.runCommandLocal "codex-private-session-scripts" { } ''
    mkdir -p "$out"
    cp ${./scripts/session_server}/*.py "$out/"
    cp ${../../hooks/runtime/common/codex_app_server_client.py} "$out/codex_app_server_client.py"
    PYTHONPATH="$out" PYTHONDONTWRITEBYTECODE=1 ${sessionPython}/bin/python3 -c 'import launch_private_session'
  '';

  sessionExecutable = pkgs.writeShellScript "codex-private-session" ''
    exec ${sessionPython}/bin/python3 ${sessionScripts}/launch_private_session.py "$@"
  '';

  codex = pkgs.writeShellApplication {
    name = "codex";
    bashOptions = [ ];
    excludeShellChecks = [ "SC1090" ];
    runtimeEnv = {
      NPM_CONFIG_PREFIX = "/nonexistent";
      CODEX_LAUNCHER_DEVELOPER_INSTRUCTIONS_FILE = "${interactivePreferencesFile}";
      CODEX_LAUNCHER_WORKSPACE_PROFILE_DISPATCH_FILE = "${workspaceProfileLaunchDispatchFile}";
      CODEX_LAUNCHER_BINARY = "${codex-unwrapped}/bin/codex";
      CODEX_LAUNCHER_HOOK_TRUST_EXECUTABLE = "${hookTrustExecutable}";
      CODEX_LAUNCHER_SESSION_EXECUTABLE = "${sessionExecutable}";
    };
    text = builtins.readFile ./scripts/codex;
  };
in
{
  options.codex.unwrappedPackage = lib.mkOption {
    type = lib.types.package;
    default = codex-unwrapped;
    readOnly = true;
    description = "The bare upstream codex binary, without the interactive wrapper that selects the human's instruction profile and injects sandbox mode and approval policy. An autonomous harness builds its own full argv and must launch this, because re-passing a flag the wrapper already injected makes codex exit 2.";
  };

  config.home = {
    packages = [ codex ];
    activation.seedCodexProfilesAsMutableFiles = lib.hm.dag.entryAfter [ "linkGeneration" ] (
      workspaceProfileActivation.seedProfiles config.agentWorkspaceProfiles.profiles
    );
    file = workspaceProfileActivation.profileFiles config.agentWorkspaceProfiles.profiles // {
      ".local/bin/codex".source = "${codex}/bin/codex";
    };
  };
}
