{ pkgs, inputs, ... }:
{
  home.packages = [
    inputs.systemd-manager-tui.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}
