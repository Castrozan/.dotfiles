{ pkgs, ... }:
let
  bitwardenSession = pkgs.writeShellApplication {
    name = "bw-session";
    runtimeInputs = [
      pkgs.bitwarden-cli
      pkgs.jq
      pkgs.coreutils
    ];
    text = builtins.readFile ./scripts/bw-session.sh;
  };
in
{
  home.packages = [
    pkgs.bitwarden-cli
    bitwardenSession
  ];

  programs.fish.shellAliases = {
    bwu = "bw-session";
  };
}
