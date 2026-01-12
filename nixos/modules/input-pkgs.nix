{ pkgs, inputs, ... }:
{
  # List of flake input packages
  environment.systemPackages = [
    #inputs.zen-browser.packages.${pkgs.stdenv.hostPlatform.system}.default
  ];
}
