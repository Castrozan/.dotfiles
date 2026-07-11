{ pkgs, lib, ... }:
{
  imports = [
    ./shared.nix
  ]
  ++ lib.optional pkgs.stdenv.hostPlatform.isDarwin ./darwin
  ++ lib.optional pkgs.stdenv.hostPlatform.isLinux ./linux;
}
