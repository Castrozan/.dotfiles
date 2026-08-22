{
  helpers,
  pkgs,
  lib,
  inputs,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  sharedDarwinConfiguration = import ../shared-darwin-system-nix-darwin.nix {
    inherit lib pkgs;
    username = "test-user";
  };
  primaryUserShellActivation =
    sharedDarwinConfiguration.system.activationScripts.postActivation.text.content or "";
  composedDarwinActivation =
    (inputs.nix-darwin.lib.darwinSystem {
      modules = [
        {
          nixpkgs.hostPlatform = "aarch64-darwin";
          system = {
            stateVersion = 6;
            activationScripts.postActivation.text = primaryUserShellActivation;
          };
        }
      ];
    }).config.system.activationScripts.script.text;
  reconcilesPrimaryUserShellToBash =
    lib.hasInfix "/usr/bin/dscl . -read /Users/test-user UserShell" composedDarwinActivation
    && lib.hasInfix "/usr/bin/dscl . -create /Users/test-user UserShell" composedDarwinActivation
    && lib.hasInfix "/run/current-system/sw/bin/bash" composedDarwinActivation
    && lib.hasInfix "/bin/timeout" composedDarwinActivation;
in
{
  darwin-primary-user-shell-is-reconciled-to-bash =
    mkEvalCheck "darwin-primary-user-shell-is-reconciled-to-bash" reconcilesPrimaryUserShellToBash
      "The shared Darwin activation must reconcile the primary admin user's directory-service shell to the stable Bash path with time-bounded dscl calls; declaring users.users.<name>.shell alone does not manage an existing admin because nix-darwin intentionally excludes primary admins from users.knownUsers, while Codex reads pw_shell through getpwuid_r and ignores the SHELL environment variable";
}
