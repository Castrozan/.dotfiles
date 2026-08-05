{
  pkgs,
  username,
  home-version,
  ...
}:
{
  imports = [
    ../operating-system/health-check/health-check-home-manager.nix
  ];

  home = {
    inherit username;
    homeDirectory =
      if pkgs.stdenv.hostPlatform.isDarwin then "/Users/${username}" else "/home/${username}";
    stateVersion = home-version;
  };
  programs.home-manager.enable = true;
  news.display = "silent";
}
