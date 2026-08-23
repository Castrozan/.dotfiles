{ pkgs, ... }:
{
  environment.systemPackages = [ (import ./python-test-environment.nix { inherit pkgs; }) ];
}
