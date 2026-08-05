{
  imports = [
    ./vpn/forticlient/forticlient-home-manager.nix
    ./network-optimization/network-optimization-home-manager.nix
    ./vpn/openfortivpn/openfortivpn-home-manager.nix
    ./tailscale/tailscale-daemon-home-manager.nix
  ];
}
