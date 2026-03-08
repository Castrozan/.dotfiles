{ pkgs, ... }:
let
  mkScript =
    name: file:
    pkgs.writeShellScriptBin name ''
      export PATH="${
        pkgs.lib.makeBinPath (
          with pkgs;
          [
            pulseaudio
            coreutils
            gnugrep
            gnused
            gawk
            util-linux
            procps
          ]
        )
      }:/usr/bin:$PATH"
      ${builtins.readFile file}
    '';
in
{
  home.packages = [
    (mkScript "hypr-theme-set" ./scripts/theme-set)
    (mkScript "hypr-theme-set-templates" ./scripts/theme-set-templates)
    (mkScript "hypr-theme-bg-apply" ./scripts/theme-bg-apply)
    (mkScript "hypr-theme-bg-next" ./scripts/theme-bg-next)
    (mkScript "hypr-theme-list" ./scripts/theme-list)
    (mkScript "hypr-theme-current" ./scripts/theme-current)
    (mkScript "hypr-theme-set-gnome" ./scripts/theme-set-gnome)
    (mkScript "hypr-restart-hyprctl" ./scripts/restart-hyprctl)
    (mkScript "hypr-menu" ./scripts/menu)
    (mkScript "hypr-fuzzel" ./scripts/fuzzel)
    (mkScript "hypr-super-launcher" ./scripts/super-launcher)
    (mkScript "hypr-launch-clipse-with-workspace-group-restoration" ./scripts/launch-clipse-with-workspace-group-restoration)
    (mkScript "hypr-ensure-workspace-tiled" ./scripts/ensure-workspace-tiled)
    (mkScript "hypr-ensure-workspace-grouped" ./scripts/ensure-workspace-grouped)
    (mkScript "hypr-all-tiled-windows-are-in-single-group" ./scripts/all-tiled-windows-are-in-single-group)
    (mkScript "hypr-close-window-cycle" ./scripts/close-window-cycle)
    (mkScript "hypr-reopen-window" ./scripts/reopen-window)
    (mkScript "hypr-reopen-window-picker" ./scripts/reopen-window-picker)
    (mkScript "hypr-show-desktop" ./scripts/show-desktop)
    (mkScript "hypr-maximize-focus-daemon" ./scripts/maximize-focus-daemon)
    (mkScript "hypr-summon-brave" ./scripts/summon-brave)
    (mkScript "hypr-detach-from-group-and-move-to-workspace" ./scripts/detach-from-group-and-move-to-workspace)
    (mkScript "hypr-toggle-group-for-all-workspace-windows" ./scripts/toggle-group-for-all-workspace-windows)
    (mkScript "hypr-screenshot" ./scripts/screenshot)
    (mkScript "hypr-network" ./scripts/network)
    (mkScript "hypr-toggle-monitors" ./scripts/toggle-monitors)
    (mkScript "hypr-monitor-hotplug-daemon" ./scripts/monitor-hotplug-daemon)
    (mkScript "hypr-notification-sound-toggle" ./scripts/notification-sound-toggle)
    (mkScript "hypr-microphone-toggle" ./scripts/microphone-toggle)
    (mkScript "hypr-summon-chrome-global" ./scripts/summon-chrome-global)
  ];
}
