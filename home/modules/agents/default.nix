{
  pkgs,
  config,
  lib,
  ...
}:
let
  dotfilesAgentInstructions = ''
    # Dotfiles Agent Instructions

    ${builtins.readFile ../../../agents/core.md}
  '';
in
{
  imports = [
    ./a2a-mcp.nix
  ];

  home.file.".dotfiles/AGENTS.md".text = dotfilesAgentInstructions;
}
