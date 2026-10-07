{
  pkgs,
  username,
  home-version,
  ...
}:
{
  imports = [
    ../development/cloud-services/cloudflare-cli/cloudflare-cli-home-manager.nix
    ../operating-system/health-check/health-check-home-manager.nix
    ../media/video-production/shorts-automation-home-manager.nix
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
