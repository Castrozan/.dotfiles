{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  symbolicHotKeysConfig = import ../symbolic-hotkeys-nix-darwin.nix;
  symbolicHotKeys =
    symbolicHotKeysConfig.system.defaults.CustomUserPreferences."com.apple.symbolichotkeys".AppleSymbolicHotKeys;
in
{
  macbook-macos-input-source-switching-disabled =
    mkEvalCheck "macbook-macos-input-source-switching-disabled"
      (!symbolicHotKeys."60".enabled && !symbolicHotKeys."61".enabled)
      "input source switching hotkeys (60, 61) must be disabled so Ctrl+Space reaches terminal apps";
}
