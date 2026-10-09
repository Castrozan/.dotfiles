{
  pkgs,
  ...
}:
{
  home.packages = [ (import ./a2a-client-package.nix { inherit pkgs; }) ];
}
