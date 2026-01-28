{ ... }:
{
  imports = [
    ./claude.nix
    ./config.nix
    ./agents.nix
    ./skills.nix
    ./hooks.nix
    ./mcp.nix
    ./private.nix
  ];
}
