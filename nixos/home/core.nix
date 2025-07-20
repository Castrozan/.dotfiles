{ username, home-version, ... }:
{
  home.username = username;
  home.homeDirectory = "/home/${username}";
  home.stateVersion = home-version;
  programs.home-manager.enable = true;
  news.display = "silent";
}
