#
# TODO: move this to home manager packages
#
{ pkgs, ... }:
{
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
    yazi
    nix-prefetch-github
    dbeaver-bin
    ventoy-full
    neovim
    htop
    btop
    wget
    p7zip

    # python3

    python312
    python312Packages.pip
    python312Packages.uvicorn
    python312Packages.fastapi
    python312Packages.uv
    python312Packages.pydantic
    python312Packages.httpx

    fzf
    k6
    # TODO: check if this is the correct package
    wireguard-go
    alejandra
    nixd
    nixpkgs-fmt
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
    brave
    # Discord and vesktop to enable screensharing on wayland
    discord
    (discord.override {
      withOpenASAR = true;
      # Vencord for costumization
      withVencord = true;
    })
    docker
    firefox
    obsidian
    postman
    # Set opera to use its codecs. This enables it to display videos
    (opera.override {
      proprietaryCodecs = true;
    })
    scrcpy
    vesktop
    # Should install manually rn from github.com/phirecc/wgnord
    wgnord
    # APPS END
  ];
}
