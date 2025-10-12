{ pkgs, inputs, ... }:
{
  # List of flake input packages
  environment.systemPackages = [
    #inputs.claude-desktop.packages.${pkgs.system}.claude-desktop-with-fhs
    #inputs.zen-browser.packages.${pkgs.system}.default
  ];
}
