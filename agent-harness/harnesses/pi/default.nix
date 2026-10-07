{ pkgs, ... }:
{
  imports = [
    ./package.nix
    ./global-instructions.nix
    (import ./plugins.nix { profileDirectory = ".pi/agent"; })
  ];
  home.file.".pi/loop-guard.json".source = (pkgs.formats.json { }).generate "pi-loop-guard.json" {
    repeatFrequencyThreshold = 6;
  };
}
