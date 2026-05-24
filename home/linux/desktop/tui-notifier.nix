{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.tui-notifier.packages.${pkgs.stdenv.hostPlatform.system}.default
    (pkgs.makeDesktopItem {
      name = "tui-notifier";
      desktopName = "TUI Notifier";
      exec = "tui-notifier";
      categories = [
        "Development"
        "Network"
      ];
      comment = "TUI Notifier";
    })
  ];
}
