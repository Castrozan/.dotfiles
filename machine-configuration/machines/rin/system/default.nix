{ ... }:
{
  imports = [
    ../../shared-darwin-system-nix-darwin.nix
    ../../../network/vpn/forticlient/retire-missing-ztnafw-nix-darwin.nix
  ];

  homebrew.brews = [
    "tailscale"
  ];
}
