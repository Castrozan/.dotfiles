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
            brightnessctl
            socat
          ]
        )
      }:/usr/bin:$PATH"
      ${builtins.readFile file}
    '';
in
{
  home.packages = [
    (mkScript "hypr-theme-set" ./scripts/theme/theme-set)
    (mkScript "hypr-theme-set-templates" ./scripts/theme/theme-set-templates)
    (mkScript "hypr-theme-bg-apply" ./scripts/theme/theme-bg-apply)
    (mkScript "hypr-theme-bg-next" ./scripts/theme/theme-bg-next)
    (mkScript "hypr-theme-list" ./scripts/theme/theme-list)
    (mkScript "hypr-theme-current" ./scripts/theme/theme-current)
    (mkScript "hypr-theme-set-gnome" ./scripts/theme/theme-set-gnome)
    (mkScript "hypr-restart-hyprctl" ./scripts/utilities/restart-hyprctl)
    (mkScript "hypr-menu" ./scripts/launchers/menu)
    (mkScript "hypr-fuzzel" ./scripts/launchers/fuzzel)
    (mkScript "hypr-super-launcher" ./scripts/launchers/super-launcher)
    (mkScript "hypr-launch-clipse-with-workspace-group-restoration" ./scripts/launchers/launch-clipse-with-workspace-group-restoration)
    (mkScript "hypr-ensure-workspace-tiled" ./scripts/windows/ensure-workspace-tiled)
    (mkScript "hypr-ensure-workspace-grouped" ./scripts/windows/ensure-workspace-grouped)
    (mkScript "hypr-all-tiled-windows-are-in-single-group" ./scripts/windows/all-tiled-windows-are-in-single-group)
    (mkScript "hypr-close-window-cycle" ./scripts/windows/close-window-cycle)
    (mkScript "hypr-reopen-window" ./scripts/windows/reopen-window)
    (mkScript "hypr-reopen-window-picker" ./scripts/windows/reopen-window-picker)
    (mkScript "hypr-show-desktop" ./scripts/windows/show-desktop)
    (mkScript "hypr-maximize-focus-daemon" ./scripts/windows/maximize-focus-daemon)
    (mkScript "hypr-summon-brave" ./scripts/launchers/summon-brave)
    (mkScript "hypr-detach-from-group-and-move-to-workspace" ./scripts/windows/detach-from-group-and-move-to-workspace)
    (mkScript "hypr-toggle-group-for-all-workspace-windows" ./scripts/theme/toggle-group-for-all-workspace-windows)
    (mkScript "hypr-screenshot" ./scripts/utilities/screenshot)
    (mkScript "hypr-network" ./scripts/hardware/network)
    (mkScript "hypr-toggle-monitors" ./scripts/hardware/toggle-monitors)
    (mkScript "hypr-monitor-hotplug-daemon" ./scripts/hardware/monitor-hotplug-daemon)
    (mkScript "hypr-notification-sound-toggle" ./scripts/hardware/notification-sound-toggle)
    (mkScript "hypr-microphone-toggle" ./scripts/hardware/microphone-toggle)
    (mkScript "hypr-summon-chrome-global" ./scripts/launchers/summon-chrome-global)
    (mkScript "brightness" ./scripts/hardware/brightness)
    (mkScript "quickshell-osd-send" ./scripts/utilities/quickshell-osd-send)
  ];
}
