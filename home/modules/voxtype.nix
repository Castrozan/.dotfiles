{ pkgs, inputs, ... }:
{
  imports = [ inputs.voxtype.homeManagerModules.default ];

  programs.voxtype = {
    enable = true;
    package = inputs.voxtype.packages.${pkgs.stdenv.hostPlatform.system}.default;
    model.name = "base.en";
    hotkey.enable = false; # Use compositor keybindings instead (recommended)
    service.enable = true;
  };
}
