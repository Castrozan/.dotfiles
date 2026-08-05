{
  lib,
  pkgs,
  username,
  ...
}:
{
  system.activationScripts.postActivation.text = lib.mkAfter ''
    export USERNAME=${lib.escapeShellArg username}
    export TIMEOUT_BINARY_PATH=${lib.escapeShellArg "${pkgs.coreutils}/bin/timeout"}
    ${builtins.readFile ./scripts/configure-displays.sh}
  '';

  system.defaults.CustomUserPreferences."com.apple.CoreGraphics" = {
    DisplayUseForcedGray = 0;
    DisplayUseInvertedPolarity = 0;
  };
}
