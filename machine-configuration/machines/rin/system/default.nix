{ ... }:
{
  imports = [
    ../../shared-darwin-system-nix-darwin.nix
  ];

  homebrew.brews = [
    "tailscale"
  ];
}
