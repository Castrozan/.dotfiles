{ ... }:
{
  imports = [
    ./claude.nix
    ./channels.nix
    ./config.nix
    ./skills.nix
    ./hooks.nix
    ./mcps.nix
    ./private.nix
    ./workspace-trust.nix
    ./scripts.nix
  ];
}
