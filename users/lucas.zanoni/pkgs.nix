{
  # Dependency injection
  pkgs,
  latest,
  ...
}:
{
  home.packages =
    with pkgs;
    [
      alejandra
      bash-completion
      bat
      brave
      clipse
      curl
      delta
      discord
      docker-compose
      fastfetch
      flameshot
      fzf
      gh
      git
      gnutar
      insomnia
      jq
      kubectl
      lazydocker
      # lens TODO: fix lens, im using the snap version for now
      micronaut
      neofetch
      # nix # leave the manually installed version
      nixd
      nixfmt-rfc-style
      nodejs
      obsidian
      pipes
      postman
      redisinsight
      ripgrep-all
      tree
      unzip
      uv
      vim
      wl-clipboard
      xclip
      yamllint
      yazi
      zip
      zoxide
      zsh
    ]
    # Appending to list
    ++ (with latest; [
      claude-code
      devenv
      # gemini-cli TODO: fix gemini-cli, im using the npm version for now
    ]);
}
