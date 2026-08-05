{ pkgs, ... }:
{
  environment.systemPackages = with pkgs; [
    stremio
  ];
}
