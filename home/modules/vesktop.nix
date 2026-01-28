{ pkgs, ... }:
{
  home.packages = [ pkgs.vesktop ];
  # Vesktop (Discord) configuration - simplified to essential theme settings
  home.file.".config/vesktop/settings/settings.json".text = builtins.toJSON {
    autoUpdate = false;
    autoUpdateNotification = true;
    useQuickCss = true;
    themeLinks = [
      "https://raw.githubusercontent.com/DiscordStyles/FrostedGlass/deploy/FrostedGlass.theme.css"
    ];
    enabledThemes = [ ];
    frameless = true;
    transparent = true;
    winCtrlQ = false;
    disableMinSize = false;
    winNativeTitleBar = false;
  };
}
