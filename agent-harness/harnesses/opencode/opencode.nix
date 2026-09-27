{
  pkgs,
  lib,
  config,
  ...
}:
let
  opencodeGo = import ./go-provider.nix { inherit (config.home) homeDirectory; };
  opencode-unwrapped = import ./upstream-package.nix { inherit pkgs; };

  interactivePreferencesFile = import ./instructions/interactive-instructions.nix {
    inherit pkgs;
    inherit (config.home) homeDirectory;
  };

  interactiveSessionConfigOverlay =
    pkgs.writeText "opencode-interactive-session-config-overlay.json"
      (
        builtins.toJSON {
          instructions = [ "${interactivePreferencesFile}" ];
        }
      );

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

  authenticatedLauncher = pkgs.replaceVars ./scripts/launch_authenticated_opencode.sh {
    opencodeApiKeyFile = opencodeGo.apiKeyFile;
    opencodeUnwrapped = opencode-unwrapped;
  };

  opencode-authenticated = pkgs.writeShellScriptBin "opencode" ''
    exec ${pkgs.bash}/bin/bash ${authenticatedLauncher} "$@"
  '';

  interactiveLauncher = pkgs.replaceVars ./scripts/launch_opencode.sh {
    inherit interactiveSessionConfigOverlay workspaceProfileLaunchDispatch interactivePreferencesFile;
    opencodeAuthenticated = opencode-authenticated;
  };

  opencode = pkgs.writeShellScriptBin "opencode" ''
    exec ${pkgs.bash}/bin/bash ${interactiveLauncher} "$@"
  '';

in
{
  options.opencode.unwrappedPackage = lib.mkOption {
    type = lib.types.package;
    default = opencode-authenticated;
    readOnly = true;
    description = "opencode without the interactive wrapper that overlays the human's own reply-shape instructions through OPENCODE_CONFIG, but still exporting OPENCODE_API_KEY from the agenix secret. An autonomous harness sets its own per-agent OPENCODE_CONFIG and must launch this, because the wrapper's overlay would replace it, while a paid opencode-go model still needs the key the plain upstream binary would never read.";
  };

  config.home = {
    packages = [ opencode ];
    file.".local/bin/opencode".source = "${opencode}/bin/opencode";
  };
}
