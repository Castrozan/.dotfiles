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

  windowManagerConfig = import ../default.nix;
  windowManager = windowManagerConfig.system.defaults.CustomUserPreferences."com.apple.WindowManager";
in
{
  macbook-macos-tiling-disabled = mkEvalCheck "macbook-macos-tiling-disabled" (
    !windowManager.GloballyEnabled
  ) "macOS native tiling must be disabled to prevent window manager conflicts";

  macbook-macos-edge-drag-disabled = mkEvalCheck "macbook-macos-edge-drag-disabled" (
    !windowManager.EnableTilingByEdgeDrag
  ) "macOS edge-drag tiling must be disabled when a window manager is active";

  macbook-macos-click-show-desktop-disabled =
    mkEvalCheck "macbook-macos-click-show-desktop-disabled"
      (!windowManager.EnableStandardClickToShowDesktop)
      "click-wallpaper-to-show-desktop must be disabled to prevent accidental window hide";

  macbook-macos-option-accelerator-disabled =
    mkEvalCheck "macbook-macos-option-accelerator-disabled"
      (!windowManager.EnableTilingOptionAccelerator)
      "macOS option-drag tiling accelerator must be disabled when a window manager is active";
}
