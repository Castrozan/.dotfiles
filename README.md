<h2 align="center">Zanoni's NixOS Desktop Config</h2>

<p align="center">
  <img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/palette/macchiato.png" width="400" />
</p>

<p align="center">
   <img alt="Stargazers" src="https://img.shields.io/github/stars/castrozan/.dotfiles?style=for-the-badge&logo=starship&color=C9CBFF&logoColor=D9E0EE&labelColor=302D41">
   <a href="https://nixos.org/">
      <img src="https://img.shields.io/badge/NixOS-24.05-informational.svg?style=for-the-badge&logo=nixos&color=F2CDCD&logoColor=D9E0EE&labelColor=302D41">
   </a>
   <a href="https://github.com/ryan4yin/nixos-and-flakes-book">
      <img src="https://img.shields.io/static/v1?label=Nix Flakes&message=learning&style=for-the-badge&logo=nixos&color=DDB6F2&logoColor=D9E0EE&labelColor=302D41">
   </a>
</p>

This repository contains the setup for my development environment on both NixOS and Ubuntu. It includes scripts for installing necessary applications and configuring dotfiles to set up a new system interactively.

1. NixOS Laptop: NixOS with home-manager, hyprland, GNOME, etc.
2. Ubuntu Work Laptop: Custom scripts for installing applications and configuring dotfiles.

## Components

|                       | NixOS(Wayland) |
| --------------------- | -------------- |
| **Window Manager**    | Hyprland       |
| **Terminal Emulator** | Bash + Kitty   |


## Hyprland + Bash + Kitty

TODO: add desktop screenshots
<!-- ![](./_img/hyprland_2023-07-29_1.webp) -->

## NixOS Setup

### How to Deploy this Flake?

<!-- prettier-ignore -->
> :red_circle: **IMPORTANT**: **You should NOT deploy this flake directly on your machine :exclamation:
> It will not succeed.** This flake contains my hardware configuration(such as
> [hardware-configuration.nix](nixos/hosts/dellg15/configs/hardware-configuration.nix),
> [Nvidia Support](https://github.com/castrozan/.dotfiles/blob/main/nixos/hosts/dellg15/configs/configuration.nix#L99-L140),
> etc.) which is not suitable for your hardwares, so make sure to adapt to your config and generate your hardware-configuration file.

> To deploy this flake from NixOS's official ISO image(purest installation method), please refer to
> [nixos.org/download](https://nixos.org/download/)

- Rebuild the system configuration using flakes:

```bash
   sudo nixos-rebuild switch --flake .#zanoni
```

Replace `dellg15` with the name of your custom host if needed.

- Generate the hardware configuration for your system:

```bash
   nixos-generate-config --dir nixos/hosts/dellg15
```

## Ubuntu Setup

The company I work for uses Ubuntu as the main operating system, so I have a setup for it as well. The setup is based on a script that installs applications and configures dotfiles. The script is interactive and guides you through the installation process.

> Make sure to clone this repo on your home directory before running the install script.
```bash
make install
```

### Flags and customization

| Config | Description                                                                                                                                                       |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| -d     | using this flag the install script will follow your settings in the [declarative.sh](./declarative.sh) file so you can install only the configs and pkgs you want |

## References

Dotfiles that inspired me:

- Nix Flakes
  - [ryan4yin/nix-config](https://github.com/ryan4yin/nix-config)
  - [OfflineBot/nixos](https://github.com/OfflineBot/nixos)

[Hyprland]: https://github.com/hyprwm/Hyprland
[Kitty]: https://github.com/kovidgoyal/kitty
[Neovim]: https://github.com/neovim/neovim
[Nerd fonts]: https://github.com/ryanoasis/nerd-fonts
[catppuccin]: https://github.com/catppuccin/catppuccin
[Yazi]: https://github.com/sxyazi/yazi