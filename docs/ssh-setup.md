# SSH Setup Documentation

## Overview
Bidirectional SSH between NixOS PC and Android phone (Termux), with local and remote access via Tailscale.

## PC Configuration (NixOS)

### SSH Server
- Enabled in `users/zanoni/nixos.nix`
- Port 22 open in firewall
- PubkeyAuthentication enabled
- Phone's public key in authorized_keys

### Secret Management (Agenix)
- Phone's private key encrypted with agenix: `secrets/id_ed25519_phone.age`
- Decrypted at runtime to `/run/agenix/id_ed25519_phone`
- Conditional config - rebuilds work even without secret file
- Edit with: `agenix-edit-phone` (script in PATH)

### SSH Client Config (`users/zanoni/home/ssh.nix`)
- `ssh phone` - local network (192.168.7.8:8022)
- `ssh phone-remote` - via Tailscale (100.79.224.17:8022)
- Known hosts managed declaratively

## Phone Configuration (Termux)

### SSH Server
- Port 8022 (Termux default)
- PC's public key in `~/.ssh/authorized_keys`

### SSH Client Config
Create `~/.ssh/config`:
```
Host zanoni
    HostName 100.94.11.81
    User zanoni
    IdentityFile ~/.ssh/id_ed25519
```
Then use: `ssh zanoni`

## Remote Access (Tailscale)

### Setup
- Module: `nixos/modules/tailscale.nix`
- Service auto-starts on boot
- PC IP: 100.94.11.81
- Phone IP: 100.79.224.17

### Usage
- PC to phone: `ssh phone-remote`
- Phone to PC: `ssh zanoni` (after config setup)

## Key Files
- `users/zanoni/nixos.nix` - SSH server, firewall, agenix config
- `users/zanoni/home/ssh.nix` - SSH client config
- `secrets/id_ed25519_phone.age` - Encrypted phone private key
- `secrets/secrets.nix` - Agenix public keys
- `nixos/modules/tailscale.nix` - Tailscale VPN config
- `bin/agenix-edit-phone` - Script to edit encrypted key

## Commands
- Rebuild: `./bin/rebuild`
- Edit phone key: `agenix-edit-phone`
- Check Tailscale: `tailscale status`
- Test connection: `ssh phone` or `ssh phone-remote`
