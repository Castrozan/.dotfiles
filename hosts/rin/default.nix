{ ... }:
{
  imports = [
    ../shared-darwin-configuration.nix
  ];

  homebrew.brews = [
    "tailscale"
  ];
}
