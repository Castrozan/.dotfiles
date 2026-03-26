{
  pkgs,
  username,
  home-version,
  ...
}:
{
  home = {
    inherit username;
    homeDirectory = "/home/${username}";
    stateVersion = home-version;
  };
  programs.home-manager.enable = true;
  news.display = "silent";
}
