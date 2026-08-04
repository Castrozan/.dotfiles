{ pkgs, hostname, ... }:
{
  environment.systemPackages = [
    (import ../../../home/base/system/scripts/rebuild { inherit pkgs hostname; })
  ];
}
