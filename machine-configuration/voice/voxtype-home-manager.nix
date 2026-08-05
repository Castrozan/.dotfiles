{ pkgs, inputs, ... }:
{
  imports = [ inputs.voxtype.homeManagerModules.default ];

  programs.voxtype = {
    enable = true;
    package = inputs.voxtype.packages.${pkgs.stdenv.hostPlatform.system}.default;
    model.name = "base.en";
    service.enable = true;
  };
}
