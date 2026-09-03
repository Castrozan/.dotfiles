{ ... }:
{
  imports = [
    ../../shared-darwin-system-nix-darwin.nix
    ../../../network/ipv6/ipv6-link-local-nix-darwin.nix
  ];

  services.tailscale.enable = true;

  homebrew.casks = [
    "claude"
    "codex-app"
    "firefox"
    "mongodb-compass"
  ];
}
