{
  inputs,
  pkgs,
  lib,
  username,
  unstable,
  latest,
  home-version,
  nixpkgs-version,
  ...
}:
{
  imports = [
    ../../users/${username}/home.nix
  ];

  home = {
    inherit username;
    homeDirectory = "/home/${username}";
    stateVersion = home-version;
  };

  programs.home-manager.enable = true;
  news.display = "silent";
}
