{ ... }:
{
  imports = [
    ./package.nix
    ./config.nix
    ./hooks
    ./rules.nix
    ./skills.nix
    ./claude-plugin-port.nix
    ./global-instructions.nix
  ];
}
