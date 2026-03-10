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

  hyprlandWindowsPythonLibraryPath = ./scripts/windows/lib;

  mkPythonWindowScript =
    name: file:
    let
      pythonSource = pkgs.writeText "${name}-source.py" (builtins.readFile file);
    in
    pkgs.writeShellScriptBin name ''
      export PYTHONPATH="${hyprlandWindowsPythonLibraryPath}:''${PYTHONPATH:-}"
      exec ${pkgs.python312}/bin/python3 ${pythonSource} "$@"
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
    (mkScript "hypr-summon-brave" ./scripts/launchers/summon-brave)
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

    (mkPythonWindowScript "hypr-maximize-focus-daemon" ./scripts/windows/maximize_focus_daemon.py)
    (mkPythonWindowScript "hypr-close-window-cycle" ./scripts/windows/close_window_cycle.py)
    (mkPythonWindowScript "hypr-reopen-window" ./scripts/windows/reopen_window.py)
    (mkPythonWindowScript "hypr-reopen-window-picker" ./scripts/windows/reopen_window_picker.py)
    (mkPythonWindowScript "hypr-show-desktop" ./scripts/windows/show_desktop.py)
    (mkPythonWindowScript "hypr-detach-from-group-and-move-to-workspace" ./scripts/windows/detach_from_group_and_move_to_workspace.py)
    (mkPythonWindowScript "hypr-all-tiled-windows-are-in-single-group" ./scripts/windows/all_tiled_windows_are_in_single_group.py)
    (mkPythonWindowScript "hypr-ensure-workspace-grouped" ./scripts/windows/ensure_workspace_grouped.py)
    (mkPythonWindowScript "hypr-ensure-workspace-tiled" ./scripts/windows/ensure_workspace_tiled.py)
  ];
}
