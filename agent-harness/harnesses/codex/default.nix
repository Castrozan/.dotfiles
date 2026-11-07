{ ... }:
{
  imports = [
    ./package/wrapper.nix
    ./config.nix
    ./rules.nix
    ./plugins.nix
    ./global-instructions.nix
    ../../workspace-profiles
  ];
}
