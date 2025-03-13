{ config, pkgs, lib, ... }:

{
  home.packages = with pkgs; [
    (makeDesktopItem {
      name = "claude-desktop";
      desktopName = "Claude Desktop";
      exec = "${pkgs.chromium}/bin/chromium --app=https://claude.ai";
      icon = builtins.fetchurl {
        url = "https://claude.ai/favicon.ico";
        # TODO: Replace with actual sha strategy
        sha256 = "1qw5w3c2v6clyv608kizpppyz501v29cnmlmibz51szgif15asl1";
      };
      categories = [
        "Development"
        "Network"
      ];
      comment = "Claude AI Desktop Application";
    })
  ];
}
