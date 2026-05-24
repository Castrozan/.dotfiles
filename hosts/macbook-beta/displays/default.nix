{
  lib,
  username,
  ...
}:
{
  system.activationScripts.postActivation.text = lib.mkAfter ''
    export USERNAME=${lib.escapeShellArg username}
    ${builtins.readFile ./configure-displays.sh}
  '';

  system.defaults.CustomUserPreferences."com.apple.CoreGraphics" = {
    DisplayUseForcedGray = 0;
    DisplayUseInvertedPolarity = 0;
  };
}
