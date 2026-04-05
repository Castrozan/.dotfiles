{ ... }:
{
  imports = [
    ./claude.nix
    ./channels.nix
    ./config.nix
    ./skills.nix
    ./external-skill-sets.nix
    ./test-forks.nix
    ./hooks.nix
    ./mcps.nix
    ./private.nix
    ./workspace-trust.nix
    ./scripts.nix
  ];
}
