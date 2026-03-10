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

  hyprlandPythonLibraryPath = ./scripts/windows/lib;

  mkHyprlandPythonScript =
    name: file:
    let
      pythonSource = pkgs.writeText "${name}-source.py" (builtins.readFile file);
    in
    pkgs.writeShellScriptBin name ''
      export PYTHONPATH="${hyprlandPythonLibraryPath}:''${PYTHONPATH:-}"
      exec ${pkgs.python312}/bin/python3 ${pythonSource} "$@"
    '';
in
{
  home.packages = [
    (mkScript "hypr-theme-set" ./scripts/theme/theme-set)
    (mkHyprlandPythonScript "hypr-theme-set-templates" ./scripts/theme/theme_set_templates.py)
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
    (mkHyprlandPythonScript "hypr-summon-brave" ./scripts/launchers/summon_brave.py)
    (mkHyprlandPythonScript "hypr-toggle-group-for-all-workspace-windows" ./scripts/windows/toggle_group_for_all_workspace_windows.py)
    (mkScript "hypr-screenshot" ./scripts/utilities/screenshot)
    (mkScript "hypr-network" ./scripts/hardware/network)
    (mkHyprlandPythonScript "hypr-toggle-monitors" ./scripts/hardware/toggle_monitors.py)
    (mkHyprlandPythonScript "hypr-monitor-hotplug-daemon" ./scripts/hardware/monitor_hotplug_daemon.py)
    (mkScript "hypr-notification-sound-toggle" ./scripts/hardware/notification-sound-toggle)
    (mkScript "hypr-microphone-toggle" ./scripts/hardware/microphone-toggle)
    (mkHyprlandPythonScript "hypr-summon-chrome-global" ./scripts/launchers/summon_chrome_global.py)
    (mkScript "brightness" ./scripts/hardware/brightness)
    (mkScript "quickshell-osd-send" ./scripts/utilities/quickshell-osd-send)

    (mkHyprlandPythonScript "hypr-maximize-focus-daemon" ./scripts/windows/maximize_focus_daemon.py)
    (mkHyprlandPythonScript "hypr-close-window-cycle" ./scripts/windows/close_window_cycle.py)
    (mkHyprlandPythonScript "hypr-reopen-window" ./scripts/windows/reopen_window.py)
    (mkHyprlandPythonScript "hypr-reopen-window-picker" ./scripts/windows/reopen_window_picker.py)
    (mkHyprlandPythonScript "hypr-show-desktop" ./scripts/windows/show_desktop.py)
    (mkHyprlandPythonScript "hypr-detach-from-group-and-move-to-workspace" ./scripts/windows/detach_from_group_and_move_to_workspace.py)
    (mkHyprlandPythonScript "hypr-all-tiled-windows-are-in-single-group" ./scripts/windows/all_tiled_windows_are_in_single_group.py)
    (mkHyprlandPythonScript "hypr-ensure-workspace-grouped" ./scripts/windows/ensure_workspace_grouped.py)
    (mkHyprlandPythonScript "hypr-ensure-workspace-tiled" ./scripts/windows/ensure_workspace_tiled.py)
  ];
}
