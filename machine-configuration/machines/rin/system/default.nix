{ ... }:
{
  imports = [
    ../../../../hosts/shared-darwin-configuration.nix
  ];

  homebrew.brews = [
    "tailscale"
  ];
}
