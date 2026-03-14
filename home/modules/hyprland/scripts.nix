{ pkgs, ... }:
let
  hyprlandPythonLibraryPath = ./scripts/windows/lib;

  mkHyprlandPythonScript = name: file: mkHyprlandPythonScriptWithDeps name file [ ];

  mkHyprlandPythonScriptWithDeps =
    name: file: runtimeDeps:
    let
      pythonSource = pkgs.writeText "${name}-source.py" (builtins.readFile file);
      pathPrefix =
        if runtimeDeps != [ ] then ''export PATH="${pkgs.lib.makeBinPath runtimeDeps}:$PATH"'' else "";
    in
    pkgs.writeShellScriptBin name ''
      ${pathPrefix}
      export PYTHONPATH="${hyprlandPythonLibraryPath}:''${PYTHONPATH:-}"
      exec ${pkgs.python312}/bin/python3 ${pythonSource} "$@"
    '';
in
{
  home.packages = [
    (mkHyprlandPythonScript "hypr-theme-set" ./scripts/theme/theme_set.py)
    (mkHyprlandPythonScript "hypr-theme-set-templates" ./scripts/theme/theme_set_templates.py)
    (mkHyprlandPythonScript "hypr-theme-bg-apply" ./scripts/theme/theme_bg_apply.py)
    (mkHyprlandPythonScript "hypr-theme-bg-next" ./scripts/theme/theme_bg_next.py)
    (mkHyprlandPythonScript "hypr-theme-list" ./scripts/theme/theme_list.py)
    (mkHyprlandPythonScript "hypr-theme-current" ./scripts/theme/theme_current.py)
    (mkHyprlandPythonScript "hypr-theme-set-gnome" ./scripts/theme/theme_set_gnome.py)
    (mkHyprlandPythonScript "hypr-restart-hyprctl" ./scripts/utilities/restart_hyprctl.py)
    (mkHyprlandPythonScript "hypr-apply-theme-colors" ./scripts/utilities/apply_theme_colors.py)
    (mkHyprlandPythonScript "hypr-menu" ./scripts/launchers/menu.py)
    (mkHyprlandPythonScript "hypr-fuzzel" ./scripts/launchers/fuzzel_launcher.py)
    (mkHyprlandPythonScript "hypr-super-launcher" ./scripts/launchers/super_launcher.py)
    (mkHyprlandPythonScript "hypr-launch-clipse-with-workspace-group-restoration" ./scripts/launchers/launch_clipse_with_workspace_group_restoration.py)
    (mkHyprlandPythonScript "hypr-summon-brave" ./scripts/launchers/summon_brave.py)
    (mkHyprlandPythonScript "hypr-toggle-group-for-all-workspace-windows" ./scripts/windows/toggle_group_for_all_workspace_windows.py)
    (mkHyprlandPythonScript "hypr-screenshot" ./scripts/utilities/screenshot.py)
    (mkHyprlandPythonScript "hypr-network" ./scripts/hardware/network.py)
    (mkHyprlandPythonScript "hypr-toggle-monitors" ./scripts/hardware/toggle_monitors.py)
    (mkHyprlandPythonScript "hypr-monitor-hotplug-daemon" ./scripts/hardware/monitor_hotplug_daemon.py)
    (mkHyprlandPythonScriptWithDeps "hypr-notification-sound-toggle"
      ./scripts/hardware/notification_sound_toggle.py
      [
        pkgs.pulseaudio
      ]
    )
    (mkHyprlandPythonScriptWithDeps "hypr-microphone-toggle" ./scripts/hardware/microphone_toggle.py [
      pkgs.pulseaudio
    ])
    (mkHyprlandPythonScript "hypr-summon-chrome-global" ./scripts/launchers/summon_chrome_global.py)
    (mkHyprlandPythonScriptWithDeps "brightness" ./scripts/hardware/brightness.py [
      pkgs.brightnessctl
    ])
    (mkHyprlandPythonScript "quickshell-osd-send" ./scripts/utilities/quickshell_osd_send.py)

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
