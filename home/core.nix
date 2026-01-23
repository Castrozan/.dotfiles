{ username, home-version, ... }: # Dependency injection
{
  home = {
    inherit username;
    homeDirectory = "/home/${username}";
    stateVersion = home-version;
  };
  programs.home-manager.enable = true; # Enable home-manager to manage itself
  news.display = "silent";
}
