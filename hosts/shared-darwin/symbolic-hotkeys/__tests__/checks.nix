{
  pkgs,
  lib,
  ...
}:
let
  helpers = import ../../../../__tests__/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = null;
    nixpkgs-version = null;
    home-version = null;
  };
  inherit (helpers) mkEvalCheck;

  symbolicHotKeysConfig = import ../default.nix;
  symbolicHotKeys =
    symbolicHotKeysConfig.system.defaults.CustomUserPreferences."com.apple.symbolichotkeys".AppleSymbolicHotKeys;
in
{
  macbook-macos-input-source-switching-disabled =
    mkEvalCheck "macbook-macos-input-source-switching-disabled"
      (!symbolicHotKeys."60".enabled && !symbolicHotKeys."61".enabled)
      "input source switching hotkeys (60, 61) must be disabled so Ctrl+Space reaches terminal apps";
}
