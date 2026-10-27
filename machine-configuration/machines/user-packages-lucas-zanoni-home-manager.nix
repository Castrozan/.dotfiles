{
  # Dependency injection
  pkgs,
  lib,
  latest,
  ...
}:
{
  home.packages =
    with pkgs;
    [
      awscli2
      alejandra
      bash-completion
      bat
      bats
      (import ../development/development-environments/bun-package.nix { inherit latest; })
      cargo
      curl
      delta
      docker-compose
      duckdb
      dust
      eza
      fastfetch
      fd
      fzf
      gdrive3
      gh
      git
      gnutar
      go

      insomnia
      jq
      kubectl
      # lens TODO: fix lens, im using the snap version for now
      micronaut
      mongosh
      # nix # leave the manually installed version
      nix-output-monitor
      (import ../development/system-rebuild/nh-package.nix { inherit pkgs; })
      nixd
      nixfmt-rfc-style
      nodejs_22
      prettier
      obsidian
      ollama
      pipes
      postman
      postgresql
      ripgrep-all
      ruff
      rustc
      shellcheck
      shfmt
      latest.tailscale
      tealdeer
      tree
      unzip
      uv
      vim
      whisper-cpp
      yamllint
      zip
      zoxide
    ]
    ++ lib.optionals pkgs.stdenv.hostPlatform.isDarwin (
      with pkgs;
      [
        (import ../operating-system/resource-monitoring/btop-package.nix { inherit pkgs; })
      ]
    )
    ++ lib.optionals pkgs.stdenv.hostPlatform.isLinux (
      with pkgs;
      [
        brave
        cava
        gnome-shell-extensions
        gnome-extension-manager
        gnomeExtensions.default-workspace
        gnomeExtensions.workspace-matrix
        imv
        i2p
        i2pd
        i2pd-tools
        playerctl
        pavucontrol
        pulsemixer
        quickemu
        redisinsight
        wiremix
        wl-clipboard
        wtype
        xclip
        ydotool
      ]
    )
    # Appending to list
    ++ (with latest; [
      lazydocker
      # gemini-cli TODO: fix gemini-cli, im using the npm version for now
      suwayomi-server
    ]);
}
