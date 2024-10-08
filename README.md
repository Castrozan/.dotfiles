# My Dotfiles

This repository contains the setup for my development environment on both Ubuntu and NixOS. It includes scripts for installing necessary applications and configuring dotfiles to set up a new system interactively.

## NixOS Setup

In the `nixos/` directory, you’ll find my NixOS configuration. These configs are based on Nix flakes with Home Manager, although some parts still rely on the older `configuration.nix` format as I migrate fully to flakes.

Currently, the setup is configured for user `zanoni` on my Dell G15 laptop. To use these dotfiles with your own system, modify the username to your liking in the flake configuration, and you can also generate a new hardware-specific configuration for your system.

- Rebuild the system configuration using flakes:

   ```bash
   sudo nixos-rebuild switch --flake .#zanoni
   ```

   Replace `dellg15` with the name of your custom host if needed.

- Generate the hardware configuration for your system:

   ```bash
   nixos-generate-config --dir nixos/hosts/dellg15
   ```

   Replace `dellg15` with your new host name and directory.

## Ubuntu Setup

For Ubuntu, the dotfiles and applications can be installed using the following command:

> Make sure to clone this repo on your home directory before running the install script.
```bash
make install
```

This script will guide you through the installation process. However, there are a few dependencies that are not automatically installed, which are noted below.
