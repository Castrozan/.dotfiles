{ pkgs, inputs, ... }:
{
  # List of flake input packages
  environment.systemPackages = [
    inputs.claude-desktop.packages.${pkgs.system}.claude-desktop-with-fhs
    inputs.codex-flake.packages.${pkgs.system}.default
  ];
}
