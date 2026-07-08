{ pkgs, inputs, ... }:
{
  programs.lazygit = {
    enable = true;
    package = inputs.lazygit.packages.${pkgs.stdenv.hostPlatform.system}.default;

    settings = {
      os = {
        shell =
          if pkgs.stdenv.hostPlatform.isDarwin then
            "${pkgs.bashInteractive}/bin/bash -c"
          else
            "${pkgs.fish}/bin/fish -i -c";
      };
    };
  };
}
