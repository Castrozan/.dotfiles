{
  pkgs,
  unstable,
  latest,
  ...
}:
{
  # List of pkgs installed from nixpkgs. To search, run: nix search wget
  environment.systemPackages =
    with pkgs;
    [
      alejandra
      ani-cli
      awscli2
      bash
      bash-completion
      bun
      btop
      cacert
      clipse
      curl
      dbeaver-bin
      deno
      discord
      (discord.override {
        withOpenASAR = true;
        withVencord = true; # For customization
      })
      docker
      fastfetch
      ffmpeg
      firefox
      fzf
      gh
      git
      google-chrome
      gnumake
      htop
      jq
      just
      k6
      ksnip
      lazydocker
      lshw
      mpv
      mpv-handler
      mpvc
      mpv-shim-default-shaders
      neofetch
      nixd
      nix-prefetch-github
      nixpkgs-fmt
      nodejs
      nodePackages.prettier
      obs-studio
      obsidian
      p7zip
      pipes
      pnpm
      poetry
      postman
      python312
      scrcpy
      sqlite
      tig # git log visualizer
      tmux
      unzip
      usbutils
      vesktop
      vim
      vlc
      wget
      wgnord # Note: Should install manually from github.com/phirecc/wgnord
      wireguard-go
      wireguard-tools
      wl-clipboard
      xclip
      yazi
      yarn
      zip
      zoxide
      zsh
    ]
    ++ (with unstable; [
      brave
      cargo
      gcc
      rustc
      rustPlatform.rustcSrc
      openssl.dev
      openssl
      SDL2
      alsa-lib.dev
      pkg-config
      supabase-cli
      terraform # Removed: its broken on nixpkgs
    ])
    ++ (with latest; [
      claude-code
      devenv
      gemini-cli
      vscode
    ]);
}
