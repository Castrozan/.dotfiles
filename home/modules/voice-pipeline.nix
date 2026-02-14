{ pkgs, inputs, ... }:
{
  imports = [ inputs.voice-pipeline.homeManagerModules.default ];

  home.packages = [
    inputs.voice-pipeline.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}
