{ pkgs, inputs, ... }:
{
  programs.lazygit = {
    enable = true;
    package = inputs.lazygit.packages.${pkgs.stdenv.hostPlatform.system}.default;

    settings = {
      os = {
        shell = "${pkgs.fish}/bin/fish -i -c";
      };
    };
  };
}
