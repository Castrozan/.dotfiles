{ ... }:
{
  imports = [
    ../shared-darwin-configuration.nix
  ];

  homebrew.brews = [
    "tailscale"
  ];

  homebrew.casks = [
    "hammerspoon"
  ];
}
