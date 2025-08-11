<h2 align="center">Zanoni's Desktop Configs</h2>

<p align="center">
  <img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/palette/macchiato.png" width="400" />
</p>

<p align="center">
   <img alt="Stargazers" src="https://img.shields.io/github/stars/castrozan/.dotfiles?style=for-the-badge&logo=starship&color=C9CBFF&logoColor=D9E0EE&labelColor=302D41">
   <a href="https://nixos.org/">
      <img src="https://img.shields.io/badge/NixOS-25.05-informational.svg?style=for-the-badge&logo=nixos&color=F2CDCD&logoColor=D9E0EE&labelColor=302D41">
   </a>
</p>

Welcome to my dotfiles! This repository contains my desktop environment setup for both **NixOS** and **Ubuntu**. It's built with Nix Flakes and Home Manager.

<!-- ## 🎬 Showcase: Hyprland + Bash/Fish + Kitty + Neovim  -->
<!-- TODO: add desktop video showcase -->
<!-- *(More screenshots & videos coming soon!)* -->

<!-- ### Hyprland -->
<!-- TODO: add screenshots -->
<!-- *Coming soon! Currently ricing with waybar and fuzzel* -->

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

## 📂 Repository Structure - Relevant things

```
.dotfiles/
├── .bashrc              # Main shell configuration (i'm using fish with [bass](https://github.com/edc/bass))
├── .config/             # Application configs (hypr, kitty, tmux, nvim, etc.)
├── .shell_env_vars      # Local environment variables (git-ignored)
├── bin/                 # Custom shell scripts & utilities
├── home/                # Home Manager modules
├── hosts/               # NixOS host configurations
├── nixos/               # NixOS system modules
├── shell/               # Shell configurations (bash, fish, zsh)
├── static/              # Wallpapers, screenshots, and other assets
├── users/               # User-specific configurations
│   ├── lucas.zanoni/    # Home Manager standalone config (Ubuntu/non-NixOS)
│   └── zanoni/          # Full NixOS system config
├── flake.nix            # Nix Flakes entry point
├── flake.lock           # Locked dependencies
├── Makefile             # Helper commands
└── README.md            # This file!
```
---

## ⚙️ Quick Start for:

<details>
<summary>
   <!-- add snowflake emoji -->
   <h2><b> NixOS Users</b></h2>
</summary>

### The Declarative Way

Got NixOS? Perfect. Here's how to deploy this flake:

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

<details>
<summary>
   <h2><b>🐧 Ubuntu/Non-NixOS Users</b></h2>
</summary>

### Home Manager Standalone

Don't have NixOS? No worries! You can still use Home Manager to manage your dotfiles:

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
nix run home-manager/release-25.05 -- --flake .#lucas.zanoni@x86_64-linux switch -b "backup-$(date +%Y-%m-%d-%H-%M-%S)"
```
</details>

---

<details>
<summary>
   <h2><b>🏗️ Architecture Overview</b></h2>
</summary>

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
        Nixpkgs["nixpkgs-25.05"]
        Unstable["nixpkgs-unstable"]
        HM["home-manager"]
        Determinate["determinate.systems"]
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
    Flake --> Determinate

    style Flake fill:#f38ba8,color:#1e1e2e
    style NixOS fill:#a6e3a1,color:#1e1e2e
    style HomeStandalone fill:#89b4fa,color:#1e1e2e
    style Nixpkgs fill:#f9e2af,color:#1e1e2e
    style HM fill:#cba6f7,color:#1e1e2e
```

</details>

---

## 🔗 Inspiration & Credits

This setup is inspired by and borrows from:
- [ryan4yin/nix-config](https://github.com/ryan4yin/nix-config) - Excellent complex Nix configurations
- [OfflineBot/nixos](https://github.com/OfflineBot/nixos) - Clean NixOS setup
- The amazing NixOS and Home Manager communities
- And countless other dotfiles repos I've stumbled upon at 3 AM 🌙

## 📚 Resources

- [NixOS Manual](https://nixos.org/manual) - Official documentation
- [Home Manager Manual](https://nix-community.github.io/home-manager/) - Home Manager docs
- [Nix Pills](https://nixos.org/guides/nix-pills/) - Learn Nix the fun way
- [NixOS & Flakes Book](https://github.com/ryan4yin/nixos-and-flakes-book) - Comprehensive guide

---

Enjoy ricing and happy hacking! If you like this setup, consider giving it a ⭐