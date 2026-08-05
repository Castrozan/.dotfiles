{ ... }:
{
  imports = [
    ./package.nix
    ./config.nix
    ./rules.nix
    ./skills.nix
    ./claude-plugin-port.nix
    ./global-instructions.nix
  ];
}
