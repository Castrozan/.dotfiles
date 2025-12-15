{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.the-editor.packages.${pkgs.system}.default
  ];
}
