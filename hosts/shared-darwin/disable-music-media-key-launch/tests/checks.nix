{
  pkgs,
  lib,
  ...
}:
let
  helpers = import ../../../../tests/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = null;
    nixpkgs-version = null;
    home-version = null;
  };
  inherit (helpers) mkEvalCheck;

  disableMusicMediaKeyLaunchConfig = import ../default.nix {
    inherit lib;
    username = "testuser";
  };
  postActivationScript =
    disableMusicMediaKeyLaunchConfig.system.activationScripts.postActivation.text.content;

  remoteControlDaemonForcedDisabled =
    lib.hasInfix "launchctl disable" postActivationScript
    && lib.hasInfix "com.apple.rcd" postActivationScript
    && lib.hasInfix "gui/" postActivationScript;
in
{
  macbook-music-media-key-launch-disabled =
    mkEvalCheck "macbook-music-media-key-launch-disabled" remoteControlDaemonForcedDisabled
      "com.apple.rcd must be launchctl-disabled in the owner's gui domain so pressing the play media key never launches Music.app";
}
