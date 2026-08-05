{ pkgs, hostname, ... }:
{
  environment.systemPackages = [
    (import ./scripts/rebuild { inherit pkgs hostname; })
  ];
}
