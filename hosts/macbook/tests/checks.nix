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

  macbook-macos-tiling-enabled =
    mkEvalCheck "macbook-macos-tiling-enabled" windowManager.GloballyEnabled
      "macOS native tiling should be enabled (yabai float mode has no conflict)";

  macbook-macos-edge-drag-enabled =
    mkEvalCheck "macbook-macos-edge-drag-enabled" windowManager.EnableTilingByEdgeDrag
      "macOS edge-drag tiling should be enabled for native window snapping";

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

  macbook-skhd-focus-cycle-prev =
    mkEvalCheck "macbook-skhd-focus-cycle-prev" (skhdHasBinding "--focus prev")
      "skhd should cycle focus with --focus prev (float-mode compatible)";

  macbook-skhd-focus-cycle-next =
    mkEvalCheck "macbook-skhd-focus-cycle-next" (skhdHasBinding "--focus next")
      "skhd should cycle focus with --focus next (float-mode compatible)";

  macbook-skhd-move-window-to-space =
    mkEvalCheck "macbook-skhd-move-window-to-space"
      (skhdHasBinding "cmd + shift - 1 : yabai -m window --space 1")
      "skhd should have cmd+shift+N bindings to move window to space N and follow focus";

  macbook-skhd-send-window-to-space =
    mkEvalCheck "macbook-skhd-send-window-to-space"
      (skhdHasBinding "cmd + alt - 1 : yabai -m window --space 1")
      "skhd should have cmd+alt+N bindings to send window to space N without following";

  macbook-skhd-kill-focused-window =
    mkEvalCheck "macbook-skhd-kill-focused-window" (skhdHasBinding "cmd - w")
      "skhd should have cmd+w binding to kill the focused window";

  macbook-skhd-no-stack-bindings = mkEvalCheck "macbook-skhd-no-stack-bindings" (
    !(skhdHasBinding "stack.prev") && !(skhdHasBinding "stack.next")
  ) "skhd must not use stack.prev/stack.next bindings (incompatible with float layout)";
}
