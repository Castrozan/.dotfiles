{
  pkgs,
  lib,
  ...
}:
let
  helpers = import ../../../tests/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = null;
    nixpkgs-version = null;
    home-version = null;
  };
  inherit (helpers) mkEvalCheck;

  yabaiConfig = import ../yabai.nix;
  skhdConfig = import ../skhd.nix;

  inherit (yabaiConfig.services) yabai;
  yabaiLayout = yabai.config.layout;
  windowManager = yabaiConfig.system.defaults.CustomUserPreferences."com.apple.WindowManager";
  skhdBindings = skhdConfig.services.skhd.skhdConfig;

  extraConfigContainsRule = appName: lib.strings.hasInfix "app=\"^${appName}" yabai.extraConfig;

  skhdHasBinding = pattern: lib.strings.hasInfix pattern skhdBindings;
in
{
  macbook-yabai-enabled =
    mkEvalCheck "macbook-yabai-enabled" yabai.enable
      "yabai window manager should be enabled";

  macbook-yabai-float-layout = mkEvalCheck "macbook-yabai-float-layout" (
    yabaiLayout == "float"
  ) "yabai must use float layout to avoid WindowManager resize conflicts";

  macbook-macos-tiling-disabled = mkEvalCheck "macbook-macos-tiling-disabled" (
    !windowManager.GloballyEnabled
  ) "macOS native tiling must be disabled to prevent z-order/focus desync with yabai";

  macbook-macos-edge-drag-disabled = mkEvalCheck "macbook-macos-edge-drag-disabled" (
    !windowManager.EnableTilingByEdgeDrag
  ) "macOS edge-drag tiling must be disabled when yabai manages windows";

  macbook-macos-click-show-desktop-disabled =
    mkEvalCheck "macbook-macos-click-show-desktop-disabled"
      (!windowManager.EnableStandardClickToShowDesktop)
      "click-wallpaper-to-show-desktop must be disabled to prevent accidental window hide";

  macbook-macos-option-accelerator-disabled =
    mkEvalCheck "macbook-macos-option-accelerator-disabled"
      (!windowManager.EnableTilingOptionAccelerator)
      "macOS option-drag tiling accelerator must be disabled when yabai manages windows";

  macbook-yabai-system-settings-unmanaged =
    mkEvalCheck "macbook-yabai-system-settings-unmanaged" (extraConfigContainsRule "System Settings$")
      "System Settings should be unmanaged by yabai";

  macbook-yabai-finder-unmanaged =
    mkEvalCheck "macbook-yabai-finder-unmanaged" (extraConfigContainsRule "Finder$")
      "Finder should be unmanaged by yabai";

  macbook-yabai-calculator-unmanaged =
    mkEvalCheck "macbook-yabai-calculator-unmanaged" (extraConfigContainsRule "Calculator$")
      "Calculator should be unmanaged by yabai";

  macbook-skhd-enabled =
    mkEvalCheck "macbook-skhd-enabled" skhdConfig.services.skhd.enable
      "skhd hotkey daemon should be enabled";

  macbook-skhd-move-window-to-space =
    mkEvalCheck "macbook-skhd-move-window-to-space"
      (skhdHasBinding "cmd + shift - 1 : yabai -m window --space 1")
      "skhd should have cmd+shift+N bindings to move window to space N and follow focus";

  macbook-skhd-send-window-to-space =
    mkEvalCheck "macbook-skhd-send-window-to-space"
      (skhdHasBinding "cmd + alt - 1 : yabai -m window --space 1")
      "skhd should have cmd+alt+N bindings to send window to space N without following";

  macbook-skhd-close-focused-window =
    mkEvalCheck "macbook-skhd-close-focused-window" (skhdHasBinding "cmd - w : yabai -m window --close")
      "skhd cmd+w must use yabai --close (not kill -9 which destroys the entire app)";

  macbook-skhd-no-kill-signal = mkEvalCheck "macbook-skhd-no-kill-signal" (
    !(skhdHasBinding "kill -9")
  ) "skhd must never use kill -9 (destroys apps instead of closing windows gracefully)";

  macbook-skhd-no-stack-bindings = mkEvalCheck "macbook-skhd-no-stack-bindings" (
    !(skhdHasBinding "stack.prev") && !(skhdHasBinding "stack.next")
  ) "skhd must not use stack.prev/stack.next bindings (incompatible with float layout)";
}
