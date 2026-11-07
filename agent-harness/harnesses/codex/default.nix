{ ... }:
{
  imports = [
    ./package/wrapper.nix
    ./config.nix
    ./rules.nix
    ./plugins.nix
    ./global-instructions.nix
    ./subagents.nix
    ../../workspace-profiles
  ];
}
