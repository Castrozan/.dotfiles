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
      cbonsai
      clipse
      curl
      delta
      docker-compose
      flameshot
      fzf
      gh
      git
      gnutar
      insomnia
      kubectl
      lazydocker
      # lens TODO: fix lens, im using the snap version for now
      neofetch
      nix
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
      direnv
      # gemini-cli TODO: fix gemini-cli, im using the npm version for now
      vscode
    ]);
}
