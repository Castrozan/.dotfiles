# NixOS Setup Guide

This guide explains how to deploy the NixOS configuration from this repository using Nix Flakes. The configuration is designed for systems running NixOS.

## NixOS Configuration Diagram

Here's a high-level overview of how the NixOS configuration is structured:

```mermaid
graph TD
    subgraph "flake.nix (Entry Point)"
        Flake[nixosConfigurations.zanoni]
    end

    subgraph "Host Configuration"
        Host[./hosts/dellg15]
    end

    subgraph "User Configuration (zanoni)"
        UserNixOS[./users/zanoni/nixos.nix]
        UserHome[./users/zanoni/home.nix]
    end

    subgraph "External Modules"
        HomeManager["home-manager"]
        Determinate["determinate.systems"]
    end

    subgraph "Custom Modules"
        CustomModules[./modules]
    end


    Flake -- imports --> Host
    Flake -- imports --> UserNixOS
    Flake -- imports & configures --> HomeManager
    Flake -- imports --> Determinate
    
    HomeManager -- uses --> UserHome

    Host -- may import --> CustomModules
    UserNixOS -- may import --> CustomModules

    style Flake fill:#844,color:white
    style Host fill:#484,color:white
    style UserNixOS fill:#448,color:white
    style UserHome fill:#448,color:white
    style HomeManager fill:#864,color:white
    style Determinate fill:#864,color:white
    style CustomModules fill:#488,color:white

```

## Prerequisites

Before you begin, make sure you have:
- A NixOS system installed (the GNOME, 64-bit Intel/AMD option is recommended for beginners).
- Nix Flakes enabled on your system. (Add `experimental-features = nix-command flakes` to `/etc/nix/nix.conf` if needed.)

## Steps to Deploy

### 1. **Clone the repo into your home directory.**

### 2. Review Host and User Configurations

Take a look at the following directories:
- **nixos/hosts:** Contains configuration examples for different machines. Use these as a template for your own host configuration.
- **nixos/users:** Includes user-specific configurations. The `zanoni` example can serve as a model for creating your own setup.

### 3. Generate Hardware Configuration

Create a hardware configuration to your system. Replace `your_host` with your machine's identifier (e.g., for a Dell G15):
```bash
nixos-generate-config --dir nixos/hosts/your_host/configs
```
This command generates a `hardware-configuration.nix` file that NixOS uses for hardware-specific settings.

### 4. Build and Deploy the Flake

Replace the user and host on the nixosConfigurations module in the [flake](/nixos/flake.nix) and run the flake: Replace `your_user` with your username (e.g., `zanoni`):
```bash
sudo nixos-rebuild switch --flake .#your_user
```
This command applies the configuration defined in the flake to your system.

### 5. Post-Deployment

After deployment:
- Restart your machine if required.
- Verify that the new settings are active.
- Continue tweaking your configurations to fit your workflow.

## Troubleshooting & Tips

- **Additional Resources:** Visit the [NixOS Manual](https://nixos.org/manual) for comprehensive documentation.
