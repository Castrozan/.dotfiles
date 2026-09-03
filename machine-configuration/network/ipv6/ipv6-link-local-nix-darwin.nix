{ lib, pkgs, ... }:
{
  system.activationScripts.postActivation.text = lib.mkAfter ''
    ${pkgs.python312}/bin/python3 ${./scripts/set_wifi_ipv6_link_local.py} || echo "Wi-Fi IPv6 link-local reconciliation failed; continuing activation" >&2
  '';
}
