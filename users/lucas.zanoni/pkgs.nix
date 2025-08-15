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
      # (code-cursor.overrideAttrs (old: {
      #   version = "1.4.2";
      #   src = pkgs.appimageTools.extract {
      #     pname = "code-cursor";
      #     version = "1.4.2";
      #     src = pkgs.fetchurl {
      #       url = "https://downloads.cursor.com/production/d01860bc5f5a36b62f8a77cd42578126270db343/linux/x64/Cursor-1.4.2-x86_64.AppImage";
      #       sha256 = "sha256-WMZA0CjApcSTup4FLIxxaO7hMMZrJPawYsfCXnFK4EE=";
      #     };
      #   };
      #   sourceRoot = "code-cursor-1.4.2-extracted/usr/share/cursor";
      # }))
      code-cursor
      devenv
      direnv
      # gemini-cli TODO: fix gemini-cli, im using the npm version for now
      vscode
    ]);
}
