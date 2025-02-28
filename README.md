<h2 align="center">Zanoni's Desktop Configs</h2>

<p align="center">
  <img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/palette/macchiato.png" width="400" />
</p>

<p align="center">
   <img alt="Stargazers" src="https://img.shields.io/github/stars/castrozan/.dotfiles?style=for-the-badge&logo=starship&color=C9CBFF&logoColor=D9E0EE&labelColor=302D41">
   <a href="https://nixos.org/">
      <img src="https://img.shields.io/badge/NixOS-24.11-informational.svg?style=for-the-badge&logo=nixos&color=F2CDCD&logoColor=D9E0EE&labelColor=302D41">
   </a>
   <a href="https://github.com/ryan4yin/nixos-and-flakes-book">
      <img src="https://img.shields.io/static/v1?label=Nix Flakes&message=learning&style=for-the-badge&logo=nixos&color=DDB6F2&logoColor=D9E0EE&labelColor=302D41">
   </a>
</p>

This repository contains the setup for my desktop environment on both NixOS and Ubuntu. It includes scripts for installing necessary applications and configuring dotfiles to set up a new system.

## 🎬 Showcase: Hyprland + Bash + Kitty + Neovim 
*(More screenshots & videos coming soon!)*
<!-- TODO: add desktop video showcase -->

### Hyprland
<!-- TODO: add screenshots -->

### Kitty ᓚᘏᗢ

<details>
<summary>🪟 Panes</summary>

![panes](docs/img/tmux/showcase-panes.png)

</details>
<details>
<summary>🪴 Screensaver</summary>

![screensaver](docs/img/tmux/showcase-screensaver.png)

</details>
<details>
<summary>🔱 Sessions</summary>

![sessions](docs/img/tmux/showcase-sessions.png)

</details>

### Neovim

<details>
<summary>:wq Editor</summary>

![editor](docs/img/neovim/showcase-editor.png)

</details>
<details>
<summary>🎯 Focused Editor</summary>

![editor](docs/img/neovim/showcase-focused-editor.png)

</details>

## 📂 Repository Structure

- **README.md** – Quick start & overview (this file)
- **docs/** – Detailed guides:
  - [NixOS Setup](docs/nixos.md)
  - [Ubuntu Setup](docs/ubuntu.md)
  - [Components & Showcase](docs/components.md)
- **nixos/** – NixOS configurations (hosts, users, etc.)
- **ubuntu/** – This does not exists since it's all scattered around (*.rc, .config, bin, etc.)

## ⚙️ Quick Start

### NixOS Users
1. **Clone the repo into your home directory.**
2. **Generate Hardware Config:**
   Replace [my hosts](nixos/hosts) with `your_host`:
   ```bash
   nixos-generate-config --dir nixos/hosts/your_host/configs
   ```
3. **Update Users:**
   Replace [my users](nixos/users) with `your_user` directory:

3. **Deploy the Flake:**
   Replace the user and host on the nixosConfigurations module and run the flake:
   ```bash
   sudo nixos-rebuild switch --flake .#your_user
   ```

_For more details, see [NixOS Setup](docs/nixos.md)._

### Ubuntu Users
1. **Clone the repo into your home directory.**
2. **Run the installer:**
   ```bash
   make install
   ```
   Use the `-d` flag to install only selected configurations (see [docs/ubuntu.md](docs/ubuntu.md) for details).

## 🔗 Inspiration
This setup is inspired by projects like:
- [ryan4yin/nix-config](https://github.com/ryan4yin/nix-config)
- [OfflineBot/nixos](https://github.com/OfflineBot/nixos)
- and many others, sorry there are too many i don't remember.

Enjoy ricing and happy hacking!