<h2 align="center"><a href="https://github.com/castrozan" target="_blank" rel="noopener noreferrer">Zanoni's</a> Desktop Configs</h2>

<p align="center">
  <img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/palette/macchiato.png" width="400" />
</p>

<p align="center">
   <a href="https://github.com/Castrozan/.dotfiles/actions/workflows/ci.yml">
      <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/castrozan/.dotfiles/ci.yml?style=for-the-badge&logo=github-actions&color=A6E3A1&logoColor=D9E0EE&labelColor=302D41&label=CI">
   </a>
   <a href="https://castrozan.github.io/.dotfiles/">
      <img alt="Coverage" src="https://img.shields.io/badge/Coverage-Report-informational.svg?style=for-the-badge&logo=codecov&color=89B4FA&logoColor=D9E0EE&labelColor=302D41">
   </a>
   <img alt="Stargazers" src="https://img.shields.io/github/stars/castrozan/.dotfiles?style=for-the-badge&logo=starship&color=C9CBFF&logoColor=D9E0EE&labelColor=302D41">
   <a href="https://nixos.org/">
      <img src="https://img.shields.io/badge/NixOS-25.11-informational.svg?style=for-the-badge&logo=nixos&color=F2CDCD&logoColor=D9E0EE&labelColor=302D41">
   </a>
</p>

Welcome to my dotfiles! This repository contains my desktop environment setup for both **NixOS** and **Ubuntu**. It's built with Nix Flakes and Home Manager.

![screensaver](static/docs/tmux/showcase-screensaver.png)

<!-- ## 🎬 Showcase: Hyprland + Bash/Fish + Kitty + Neovim  -->
<!-- TODO: add desktop video showcase -->
<!-- *(More screenshots & videos coming soon!)* -->

<!-- ### Hyprland -->
<!-- TODO: add screenshots -->
<!-- *Coming soon! Currently ricing with waybar and fuzzel* -->

## Desktop Showcase

### Kitty ᓚᘏᗢ + Tmux

<details>
<summary>🪟 Panes</summary>

![panes](static/docs/tmux/showcase-panes.png)

</details>
<details>
<summary>🪴 Screensaver</summary>

![screensaver](static/docs/tmux/showcase-screensaver.png)

</details>
<details>
<summary>🔱 Sessions</summary>

![sessions](static/docs/tmux/showcase-sessions.png)

</details>

### Neovim

<details>
<summary>:wq Editor</summary>

![editor](static/docs/neovim/showcase-editor.png)

</details>
<details>
<summary>🎯 Focused Editor</summary>

![editor](static/docs/neovim/showcase-focused-editor.png)

</details>

---

## Getting Started

### The Declarative Way

Got NixOS from the <a href="https://nixos.org/download.html" target="_blank" rel="noopener noreferrer">installer</a>? Perfect. Here's how to deploy this flake:

<details>
<summary>
   <b>Quick Start for: ❄️ NixOS Users</b>
</summary>

#### 1. Clone the Repository
```bash
cd ~
git clone https://github.com/castrozan/.dotfiles.git
cd .dotfiles
```

#### 2. Generate Hardware Configuration
Replace `your_host` with your machine's identifier (e.g., `dellg15`):
```bash
sudo nixos-generate-config --dir hosts/your_host/configs
```

#### 3. Customize Your Configuration
- Copy and modify a user directory from `users/` (use `zanoni` as template)
- Update `flake.nix` to add your configuration in `nixosConfigurations`

#### 4. Deploy the Flake
```bash
sudo nixos-rebuild switch --flake .#your_user
```

#### 5. Post-Deployment
- Restart your system (recommended)
- Enjoy your new setup! 🎉

</details>

---

### Home Manager Standalone

Don't wanna go full NixOS for now? No worries! You can still use the flake with Home Manager to manage your dotfiles:
<details>
<summary>
   <b>Quick Start for: 🐧 Ubuntu/Non-NixOS systems</b>
</summary>

#### 1. Clone the Repository
```bash
cd ~
git clone https://github.com/castrozan/.dotfiles.git
cd .dotfiles
```

#### 2. Install Nix (if not already installed)
```bash
curl -L https://nixos.org/nix/install | sh -s -- --daemon
```

#### 3. Deploy with Home Manager
```bash
# For the lucas.zanoni configuration (adjust username as needed)
nix run home-manager/release-25.11 -- --flake .#lucas.zanoni@x86_64-linux switch -b "backup-$(date +%Y-%m-%d-%H-%M-%S)"
```
</details>

---

## 🏗️ Architecture Overview

<details>
<summary>📦 mermaid</summary>

Here's how everything fits together:

```mermaid
graph TD
    subgraph "flake.nix"
        Flake["Entry Point<br/>defines configs"]
    end

    subgraph "NixOS Configuration"
        NixOS["nixosConfigurations.zanoni"]
        Host["hosts/dellg15<br/>hardware config"]
        UserNixOS["users/zanoni/nixos.nix"]
    end

    subgraph "Home Manager Configuration"
        HomeStandalone["homeConfigurations<br/>lucas.zanoni@x86_64-linux"]
        UserHome["users/*/home.nix"]
        Modules["home/modules/*<br/>app configs"]
    end

    subgraph "External Inputs"
        Nixpkgs["nixpkgs-25.11"]
        Unstable["nixpkgs-unstable"]
        HM["home-manager"]
    end

    Flake --> NixOS
    Flake --> HomeStandalone
    
    NixOS --> Host
    NixOS --> UserNixOS
    NixOS --> HM
    
    HomeStandalone --> UserHome
    UserHome --> Modules
    
    Flake --> Nixpkgs
    Flake --> Unstable

    style Flake fill:#f38ba8,color:#1e1e2e
    style NixOS fill:#a6e3a1,color:#1e1e2e
    style HomeStandalone fill:#89b4fa,color:#1e1e2e
    style Nixpkgs fill:#f9e2af,color:#1e1e2e
    style HM fill:#cba6f7,color:#1e1e2e
```

</details>

---

## 📂 Repository Structure - Relevant things

<details>
<summary>📂 Structure</summary>

```
.dotfiles/
├── .bashrc              # Main shell configuration (i'm using fish with bass)
├── .config/             # Application configs (hypr, kitty, tmux, nvim, etc.)
├── .shell_env_vars      # Local environment variables (git-ignored)
├── bin/                 # Custom shell scripts & utilities
├── home/                # Home Manager shared modules
├── hosts/               # NixOS hosts configuration
├── nixos/               # NixOS shared system modules
├── shell/               # Shell configurations (bash, fish, zsh)
├── users/               # User-specific configurations
│   ├── lucas.zanoni/    # Home Manager standalone config (Ubuntu/non-NixOS)
│   └── zanoni/          # Full NixOS system config
├── flake.nix            # Nix Flakes entry point
├── Makefile             # Helper commands
└── README.md            # This file!
```
</details>

---

## How to Explore Nix Options

Explore options for configurations directly from the repl so it is up to date with the rebuild command.

```bash
nix repl
```

Then in the REPL:
```nix
:lf .#homeConfigurations.lucas.zanoni@x86_64-linux
builtins.attrNames config.options.xdg.desktopEntries.type.getSubOptions
```

Or to see option descriptions:
```nix
config.options.xdg.desktopEntries.description
```
---

## 🔗 Inspiration & Credits

This setup is inspired by and borrows from:
- <a href="https://github.com/ryan4yin/nix-config" target="_blank" rel="noopener noreferrer">ryan4yin/nix-config</a> - Excellent complex Nix configurations
- <a href="https://github.com/OfflineBot/nixos" target="_blank" rel="noopener noreferrer">OfflineBot/nixos</a> - Clean NixOS setup
- The amazing NixOS and Home Manager communities
- And countless other dotfiles repos I've stumbled upon at 3 AM 🌙

## 📚 Resources

- <a href="https://nixos.org/manual" target="_blank" rel="noopener noreferrer">NixOS Manual</a> - Official documentation
- <a href="https://nix-community.github.io/home-manager/" target="_blank" rel="noopener noreferrer">Home Manager Manual</a> - Home Manager docs
- <a href="https://nixos.org/guides/nix-pills/" target="_blank" rel="noopener noreferrer">Nix Pills</a> - Learn Nix the fun way
- <a href="https://github.com/ryan4yin/nixos-and-flakes-book" target="_blank" rel="noopener noreferrer">NixOS & Flakes Book</a> - Comprehensive guide

---

Enjoy ricing and happy hacking! If you like this setup, consider giving it a ⭐