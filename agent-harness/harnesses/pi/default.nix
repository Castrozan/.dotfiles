{ ... }:
{
  imports = [
    ./package.nix
    ./global-instructions.nix
    (import ./plugins.nix { profileDirectory = ".pi/agent"; })
  ];
}
