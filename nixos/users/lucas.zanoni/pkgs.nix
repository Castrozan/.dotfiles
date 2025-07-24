{
  # Dependecy injection
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
      flameshot
      fzf
      gh
      git
      gnutar
      insomnia
      lazydocker
      lens
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
      xclip
      yazi
      zip
      zoxide
      zsh
    ]
    # Appending to list
    ++ (with latest; [
      claude-code
      code-cursor
      devenv
      direnv
      gemini-cli
      vscode
    ]);
}
