{ pkgs, ... }:
{
  home.packages = [ (import ./. { inherit pkgs; }).package ];
}
