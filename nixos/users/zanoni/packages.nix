#
# TODO: move this to home manager packages
#
{pkgs, ...}: {
  # TODO: fix this like https://www.youtube.com/watch?v=M_zMoHlbZBY
  nix.nixPath = ["nixpkgs=github:nixos/nixpkgs/nixos-24.05"];

  # List packages installed in system profile. To search, run: nix search wget
  environment.systemPackages = with pkgs; [
    # TODO: organize this
    # UTILS BEGIN
    zsh
    vim
    git
    # bash
    # bash-completion
    tmux
    gnumake
    alejandra
    yazi
    nix-prefetch-github
    dbeaver-bin
    ventoy-full
    neovim
    htop
    btop
    wget
    fzf
    k6
    # TODO: check if this is the correct package
    wireguard-go
    direnv
    nixd
    nixpkgs-fmt
    nixfmt-rfc-style
    # NordVpn Wireguard client
    linuxKernel.packages.linux_5_4.wireguard
    wireguard-tools
    ffmpeg
    gh
    unzip
    zip
    azure-cli
    terraform
    cbonsai
    pipes
    lazygit
    lazydocker
    # tmux yank depends on xsel
    xsel
    # UTILS END

    # APPS BEGIN
    docker
    scrcpy
    obsidian
    brave
    firefox
    # Set opera to use its codecs. This enables it to display videos
    (
      opera.override {
        proprietaryCodecs = true;
      }
    )
    # Should install manually rn from github.com/phirecc/wgnord
    wgnord
    # Discord and vesktop to enable screensharing on wayland
    discord
    vesktop
    # Config to enable OpenAsar / Vencord
    (
      discord.override {
        withOpenASAR = true;
        # Vencord for costumization
        withVencord = true;
      }
    )
    # APPS END
  ];
}
