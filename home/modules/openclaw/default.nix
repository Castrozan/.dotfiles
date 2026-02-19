{ ... }:
{
  imports = [
    ./orchestrator.nix
    ./deploy.nix
    ./plugins/grid.nix
    ./skills/avatar.nix
  ];
}
