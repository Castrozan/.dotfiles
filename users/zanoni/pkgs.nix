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
      just
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
      # vivaldi
      # vivaldi-ffmpeg-codecs
      # (vivaldi.override {
      #   proprietaryCodecs = true; # Enables video playback
      #   enableWidevine = true;
      # })
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
      (code-cursor.overrideAttrs (old: {
        version = "1.4.2";
        src = pkgs.appimageTools.extract {
          pname = "code-cursor";
          version = "1.4.2";
          src = pkgs.fetchurl {
            url = "https://downloads.cursor.com/production/d01860bc5f5a36b62f8a77cd42578126270db343/linux/x64/Cursor-1.4.2-x86_64.AppImage";
            sha256 = "sha256-WMZA0CjApcSTup4FLIxxaO7hMMZrJPawYsfCXnFK4EE=";
          };
        };
        sourceRoot = "code-cursor-1.4.2-extracted/usr/share/cursor";
      }))
      openshot-qt
      devenv
      direnv
      gemini-cli
      vscode
    ]);
}
