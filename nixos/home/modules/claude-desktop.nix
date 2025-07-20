{ pkgs, inputs, ... }:

{
  home.packages = [
    inputs.claude-desktop.packages.${pkgs.system}.claude-desktop-with-fhs
    (pkgs.makeDesktopItem {
      name = "claude-desktop";
      desktopName = "Claude Desktop";
      exec = "claude-desktop";
      #icon = builtins.fetchurl {
      # url = "https://claude.ai/favicon.ico";
      # TODO: Replace with actual sha strategy
      #sha256 = "1qw5w3c2v6clyv608kizpppyz501v29cnmlmibz51szgif15asl1";
      #};
      categories = [
        "Development"
        "Network"
      ];
      comment = "Claude AI Desktop Application";
    })
  ];
}
