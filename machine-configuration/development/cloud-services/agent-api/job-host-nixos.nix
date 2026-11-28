{ pkgs, ... }:
{
  environment.systemPackages = [ (import ./job-package.nix { inherit pkgs; }) ];
}
