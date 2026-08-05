{ ... }:
{
  imports = [
    ../../shared-darwin-system-nix-darwin.nix
  ];

  services.tailscale.enable = true;

  homebrew.casks = [
    "claude"
    "codex-app"
    "firefox"
    "mongodb-compass"
  ];
}
