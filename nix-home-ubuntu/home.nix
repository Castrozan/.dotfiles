{
  pkgs,
  latest,
  username,
  home-version,
  ...
}:
{
  home.username = username;
  home.homeDirectory = "/home/${username}";
  home.stateVersion = home-version;
  programs.home-manager.enable = true;
  news.display = "silent";

  imports = [
    ./modules/dooit.nix
    ./modules/gemini.nix
    # ./modules/m2.nix
    ./modules/pipx.nix
    ./modules/sdkman.nix
  ];

  home.packages = with pkgs; [
    git
    xclip
    curl
    zip
    unzip
    gnutar
    curl
    lazydocker
    ripgrep-all

    # nix formatting tools
    nixd
    nixfmt-rfc-style
    alejandra

    brave
    insomnia
    uv
    postman
    redisinsight
    lens
    latest.code-cursor
    latest.claude-code
  ];
}
