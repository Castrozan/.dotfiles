{
  pkgs,
  username,
  home-version,
  ...
}:
{
  home = {
    inherit username;
    homeDirectory = if pkgs.stdenv.isDarwin then "/Users/${username}" else "/home/${username}";
    stateVersion = home-version;
  };
  programs.home-manager.enable = true;
  news.display = "silent";
}
