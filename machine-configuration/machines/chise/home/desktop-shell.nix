{ config, ... }:
{
  custom.desktopShell = {
    active = "impasto";
    impastoInterfaceScale = 1.25;
    impastoFirstRunSettings = {
      vpnUnit = "openvpn-proton-paraguay.service";
      vpnConnectCommand = "vpn-py";
      vpnDisconnectCommand = "vpn-off";
      keyboardBacklightCommand = "set-keyboard-backlight-brightness";
      brightnessCommand = "brightness";
      wallpaperChangedCommand = "hypr-theme-generate-and-apply";
      paletteFile = "${config.xdg.configHome}/hypr-theme/current/theme/impasto-palette.json";
      barWorkspacePeekSeconds = 6;
      workspacePageSize = 7;
      workspaceStyle = "numbers";
      workspaceNumbers = "real";
    };
  };
}
