{ ... }:
{
  imports = [
    ./claude.nix
    ./config.nix
    ./skills.nix
    ./hooks.nix
    ./mcp.nix
    ./private.nix
    ./workspace-trust.nix
  ];
}
