{ pkgs, latest, ... }:
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

  mkHyprlandPythonScriptWithPythonPackages =
    name: file: pythonPackagesFn: runtimeDeps:
    let
      pythonWithPackages = pkgs.python312.withPackages pythonPackagesFn;
      pythonSource = pkgs.writeText "${name}-source.py" (builtins.readFile file);
      pathPrefix =
        if runtimeDeps != [ ] then ''export PATH="${pkgs.lib.makeBinPath runtimeDeps}:$PATH"'' else "";
    in
    pkgs.writeShellScriptBin name ''
      ${pathPrefix}
      export PYTHONPATH="${hyprlandPythonLibraryPath}:''${PYTHONPATH:-}"
      exec ${pythonWithPackages}/bin/python3 ${pythonSource} "$@"
    '';
in
{
  home.packages = [
    (mkHyprlandPythonScript "hypr-theme-set" ./scripts/theme/theme_set.py)
    (mkHyprlandPythonScript "hypr-theme-set-templates" ./scripts/theme/theme_set_templates.py)
    (mkHyprlandPythonScript "hypr-theme-bg-apply" ./scripts/theme/theme_bg_apply.py)
    (mkHyprlandPythonScript "hypr-theme-bg-next" ./scripts/theme/theme_bg_next.py)
    (mkHyprlandPythonScript "hypr-theme-set-gnome" ./scripts/theme/theme_set_gnome.py)
    (mkHyprlandPythonScriptWithPythonPackages "hypr-theme-generate-from-wallpaper"
      ./scripts/theme/theme_generate_from_wallpaper.py
      (ps: [
        ps.colorthief
        ps.pillow
      ])
      [ ]
    )
    (mkHyprlandPythonScriptWithDeps "hypr-theme-generate-and-apply"
      ./scripts/theme/theme_generate_and_apply.py
      [ pkgs.ffmpeg ]
    )
    (mkHyprlandPythonScript "hypr-restart-hyprctl" ./scripts/utilities/restart_hyprctl.py)
    (mkHyprlandPythonScript "hypr-apply-theme-colors" ./scripts/utilities/apply_theme_colors.py)
    (mkHyprlandPythonScript "hypr-menu" ./scripts/launchers/menu.py)
    (mkHyprlandPythonScript "hypr-fuzzel" ./scripts/launchers/fuzzel_launcher.py)
    (mkHyprlandPythonScript "hypr-super-launcher" ./scripts/launchers/super_launcher.py)
    (mkHyprlandPythonScript "hypr-launch-clipse" ./scripts/launchers/launch_clipse.py)
    (mkHyprlandPythonScript "hypr-summon-brave" ./scripts/launchers/summon_brave.py)
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
    (mkHyprlandPythonScriptWithDeps "hypr-summon-chrome-global"
      ./scripts/launchers/summon_chrome_global.py
      [ latest.google-chrome ]
    )
    (mkHyprlandPythonScriptWithDeps "brightness" ./scripts/hardware/brightness.py [
      pkgs.brightnessctl
    ])
    (mkHyprlandPythonScript "quickshell-osd-send" ./scripts/utilities/quickshell_osd_send.py)

    (mkHyprlandPythonScript "hypr-focus-daemon" ./scripts/windows/focus_daemon.py)
    (mkHyprlandPythonScript "hypr-close-window-cycle" ./scripts/windows/close_window_cycle.py)
    (mkHyprlandPythonScript "hypr-reopen-window" ./scripts/windows/reopen_window.py)
    (mkHyprlandPythonScript "hypr-reopen-window-picker" ./scripts/windows/reopen_window_picker.py)
    (mkHyprlandPythonScript "hypr-show-desktop" ./scripts/windows/show_desktop.py)
    (mkHyprlandPythonScript "hypr-move-window-to-workspace" ./scripts/windows/move_window_to_workspace.py)
  ];
}
