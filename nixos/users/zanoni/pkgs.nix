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
      # TCC tools
      gdrive3
      #pandoc_3_5
      haskellPackages.citeproc
      texlive.combined.scheme-full
      texliveTeTeX
      imagemagick
      convertall

      # Development Tools
      alejandra
      awscli2
      azure-cli
      dbeaver-bin
      cacert
      cypress
      docker
      gh
      git
      gnumake
      k6
      lazydocker
      nixd
      nixpkgs-fmt
      nix-prefetch-github
      nodePackages.prettier
      terraform
      tig

      # Python and Dependencies
      python312
      python312Packages.fastapi
      python312Packages.httpx
      python312Packages.pip
      python312Packages.pydantic
      python312Packages.uv
      python312Packages.uvicorn
      poetry
      # TODO: migrate this to home-manager /home/packages/playwright.nix
      playwright-driver.browsers
      playwright-driver

      # System Utilities
      btop
      ffmpeg
      fzf
      htop
      p7zip
      tmux
      unzip
      vim
      wget
      xclip
      xsel # Required for tmux yank
      yazi
      zip
      zoxide
      zsh

      # Network Tools
      linuxKernel.packages.linux_5_4.wireguard
      wgnord # Note: Should install manually from github.com/phirecc/wgnord
      wireguard-go
      wireguard-tools

      # Applications
      obs-studio
      google-chrome
      discord
      (discord.override {
        withOpenASAR = true;
        withVencord = true; # For customization
      })
      firefox
      obsidian
      vivaldi
      vivaldi-ffmpeg-codecs
      (vivaldi.override {
        proprietaryCodecs = true; # Enables video playback
        enableWidevine = true;
      })
      postman
      scrcpy
      vesktop

      # Terminal Eye Candy
      cbonsai
      pipes
      cmatrix

      vim
      wget
      curl
      git
      bash
      bash-completion
      vlc
      tmux
      usbutils
      htop
      wget
      lshw # see hardware info
      jq
      neofetch
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
    ])
    ++ (with latest; [
      claude-code
      code-cursor
      openshot-qt
      devenv
      direnv
      gemini-cli
      vscode
    ]);
}
