{ ... }:
{
  imports = [
    ./package.nix
    ./global-instructions.nix
    (import ./plugins.nix { profileDirectory = ".pi/agent"; })
  ];
  home.file.".pi/loop-guard.json".text = builtins.toJSON {
    repeatFrequencyThreshold = 6;
  };
}
