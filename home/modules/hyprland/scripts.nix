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
    (mkScript "hypr-theme-set" ../../../bin/hypr/theme-set)
    (mkScript "hypr-theme-set-templates" ../../../bin/hypr/theme-set-templates)
    (mkScript "hypr-theme-bg-next" ../../../bin/hypr/theme-bg-next)
    (mkScript "hypr-theme-list" ../../../bin/hypr/theme-list)
    (mkScript "hypr-theme-current" ../../../bin/hypr/theme-current)
    (mkScript "hypr-theme-set-gnome" ../../../bin/hypr/theme-set-gnome)
    (mkScript "hypr-restart-waybar" ../../../bin/hypr/restart-waybar)
    (mkScript "hypr-restart-hyprctl" ../../../bin/hypr/restart-hyprctl)
    (mkScript "hypr-restart-mako" ../../../bin/hypr/restart-mako)
    (mkScript "hypr-menu" ../../../bin/hypr/menu)
    (mkScript "hypr-fuzzel" ../../../bin/hypr/fuzzel)
    (mkScript "hypr-super-launcher" ../../../bin/hypr/super-launcher)
    (mkScript "hypr-bluetooth" ../../../bin/hypr/bluetooth)
    (mkScript "hypr-close-window-cycle" ../../../bin/hypr/close-window-cycle)
    (mkScript "hypr-reopen-window" ../../../bin/hypr/reopen-window)
    (mkScript "hypr-reopen-window-picker" ../../../bin/hypr/reopen-window-picker)
    (mkScript "hypr-show-desktop" ../../../bin/hypr/show-desktop)
    (mkScript "hypr-maximize-focus-daemon" ../../../bin/hypr/maximize-focus-daemon)
    (mkScript "hypr-summon-brave" ../../../bin/hypr/summon-brave)
    (mkScript "hypr-detach-from-group-and-move-to-workspace" ../../../bin/hypr/detach-from-group-and-move-to-workspace)
    (mkScript "hypr-toggle-group-for-all-workspace-windows" ../../../bin/hypr/toggle-group-for-all-workspace-windows)
    (mkScript "hypr-screenshot" ../../../bin/hypr/screenshot)
    (mkScript "hypr-network" ../../../bin/hypr/network)
    (mkScript "hypr-toggle-monitors" ../../../bin/hypr/toggle-monitors)
    (mkScript "hypr-monitor-hotplug-daemon" ../../../bin/hypr/monitor-hotplug-daemon)
    (mkScript "hypr-notification-sound-toggle" ../../../bin/hypr/notification-sound-toggle)
    (mkScript "hypr-microphone-toggle" ../../../bin/hypr/microphone-toggle)
    (mkScript "hypr-summon-chrome-global" ../../../bin/hypr/summon-chrome-global)
  ];
}
