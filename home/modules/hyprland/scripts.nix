{ pkgs, ... }:
let
  mkScript = name: file: pkgs.writeShellScriptBin name (builtins.readFile file);
in
{
  home.packages = [
    (mkScript "hypr-theme-set" ../../../bin/hypr/theme-set)
    (mkScript "hypr-theme-set-templates" ../../../bin/hypr/theme-set-templates)
    (mkScript "hypr-theme-bg-next" ../../../bin/hypr/theme-bg-next)
    (mkScript "hypr-theme-list" ../../../bin/hypr/theme-list)
    (mkScript "hypr-theme-current" ../../../bin/hypr/theme-current)
    (mkScript "hypr-theme-set-gnome" ../../../bin/hypr/theme-set-gnome)
    (mkScript "hypr-restart-waybar" ../../../bin/hypr/restart-waybar)
    (mkScript "hypr-restart-swayosd" ../../../bin/hypr/restart-swayosd)
    (mkScript "hypr-restart-hyprctl" ../../../bin/hypr/restart-hyprctl)
    (mkScript "hypr-restart-mako" ../../../bin/hypr/restart-mako)
    (mkScript "hypr-menu" ../../../bin/hypr/menu)
    (mkScript "hypr-fuzzel" ../../../bin/hypr/fuzzel)
    (mkScript "hypr-super-launcher" ../../../bin/hypr/super-launcher)
    (mkScript "hypr-bluetooth" ../../../bin/hypr/bluetooth)
    (mkScript "hypr-close-window-cycle" ../../../bin/hypr/close-window-cycle)
    (mkScript "hypr-show-desktop" ../../../bin/hypr/show-desktop)
    (mkScript "hypr-maximize-focus-daemon" ../../../bin/hypr/maximize-focus-daemon)
    (mkScript "hypr-monitor-switch" ../../../bin/hypr/monitor-switch)
    (mkScript "hypr-summon-brave" ../../../bin/hypr/summon-brave)
    (mkScript "hypr-detach-from-group-and-move-to-workspace" ../../../bin/hypr/detach-from-group-and-move-to-workspace)
    (mkScript "hypr-toggle-group-for-all-workspace-windows" ../../../bin/hypr/toggle-group-for-all-workspace-windows)
    (mkScript "hypr-screenshot" ../../../bin/hypr/screenshot)
    (mkScript "hypr-network" ../../../bin/hypr/network)
  ];
}
