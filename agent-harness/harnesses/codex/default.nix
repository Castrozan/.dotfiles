{ ... }:
{
  imports = [
    ./package.nix
    ./config.nix
    ./rules.nix
    ./plugins.nix
    ./global-instructions.nix
    ../../workspace-profiles
  ];
}
