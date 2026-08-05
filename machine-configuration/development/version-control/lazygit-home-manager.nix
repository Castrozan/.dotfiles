{ pkgs, inputs, ... }:
{
  programs.lazygit = {
    enable = true;
    package = inputs.lazygit.packages.${pkgs.stdenv.hostPlatform.system}.default;

    settings = {
      os = {
        shell = "${pkgs.bashInteractive}/bin/bash -c";
      };
    };
  };
}
