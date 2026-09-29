{
  config,
  lib,
  pkgs,
  ...
}:
{
  system.activationScripts.userDefaults.text = lib.mkAfter ''
    dockLaunchAgent="gui/$(/usr/bin/id -u ${lib.escapeShellArg config.system.primaryUser})/com.apple.Dock.agent"
    if /bin/launchctl print "$dockLaunchAgent" >/dev/null 2>&1; then
      ${pkgs.coreutils}/bin/timeout 5 /bin/launchctl kickstart -k "$dockLaunchAgent" || exit 1
    fi
  '';

  system.defaults.CustomUserPreferences."com.apple.WindowManager" = {
    EnableTiledWindowMargins = false;
    EnableTilingByEdgeDrag = false;
    EnableTilingOptionAccelerator = false;
    EnableTopTilingByEdgeDrag = false;
    EnableStandardClickToShowDesktop = false;
    GloballyEnabled = false;
    AppWindowGroupingBehavior = 1;
    AutoHide = false;
    HideDesktop = true;
    StandardHideWidgets = false;
    StageManagerHideWidgets = false;
  };
}
