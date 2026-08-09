{ pkgs, ... }:
let
  tailnetRoutePreservationPackage = pkgs.writeShellScriptBin "install-tailnet-route-in-main-routing-table" (
    builtins.readFile ./scripts/install-tailnet-route-in-main-routing-table
  );
in
{
  systemd.services.tailnet-route-preservation = {
    description = "Route the tailnet through tailscale0 in the main table so a full-tunnel NordVPN connection cannot swallow it — wg-quick installs its rules just above the tailscale rule that owns the tailnet table, so every tailnet address, MagicDNS included, otherwise disappears into the NordVPN tunnel while it is up; wg-quick consults the main table first for anything more specific than a default route, which is what makes this route survive the capture";
    after = [ "tailscaled.service" ];
    bindsTo = [ "tailscaled.service" ];
    wantedBy = [
      "tailscaled.service"
      "multi-user.target"
    ];
    path = [ pkgs.iproute2 ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = "${tailnetRoutePreservationPackage}/bin/install-tailnet-route-in-main-routing-table";
    };
  };
}
