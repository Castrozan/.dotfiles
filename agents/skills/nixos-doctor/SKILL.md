# NixOS Doctor — System Health & Troubleshooting Skill

A Clawdbot skill for diagnosing, monitoring, and fixing common NixOS issues. Built for NixOS power users who want their AI agent to understand their system deeply.

## When to Use

- System feels slow, broken, or misconfigured
- After `nixos-rebuild` failures
- Checking system health (disk, services, boot, generations)
- Diagnosing failed systemd units
- Finding orphaned packages, stale generations, or disk bloat
- Verifying Nix store integrity
- Troubleshooting Hyprland/Wayland/display issues
- Network/DNS problems

## Diagnostic Checklist

Run these in order. Stop and report when you find an issue.

### 1. Quick Vitals
```bash
# Disk usage (Nix store is usually the biggest consumer)
df -h / /nix/store 2>/dev/null || df -h /
du -sh /nix/store 2>/dev/null

# Memory & swap
free -h

# Load average
uptime

# Failed systemd units (system + user)
systemctl --failed
systemctl --user --failed

# Boot errors
journalctl -b -p err --no-pager | tail -30
```

### 2. NixOS Generations & Garbage
```bash
# List generations (look for bloat — too many old ones)
sudo nix-env --list-generations -p /nix/var/nix/profiles/system 2>/dev/null || echo "Need sudo"

# Current generation
readlink -f /run/current-system

# Count generations
ls /nix/var/nix/profiles/system-*-link 2>/dev/null | wc -l

# Nix store size
du -sh /nix/store 2>/dev/null

# Check if garbage collection would free space
nix-store --gc --print-dead 2>/dev/null | wc -l
```

**Fix: Clean old generations**
```bash
# Delete generations older than 7 days
sudo nix-collect-garbage --delete-older-than 7d

# Or keep only last N generations
sudo nix-env --delete-generations +5 -p /nix/var/nix/profiles/system
sudo nix-collect-garbage
```

### 3. Nix Store Integrity
```bash
# Verify store paths (can take a while)
nix-store --verify --check-contents 2>&1 | tail -20

# Check for missing references
nix-store --verify 2>&1 | head -20
```

**Fix: Repair corrupted paths**
```bash
nix-store --repair-path /nix/store/<hash>-<name>
# Or repair everything (slow):
sudo nix-store --verify --check-contents --repair
```

### 4. Flake & Build Health
```bash
# Check flake inputs are up to date
cd ~/.dotfiles && nix flake metadata 2>&1 | head -30

# Check for evaluation errors without building
nix flake check --no-build 2>&1 | tail -20

# Test build without switching
sudo nixos-rebuild build --flake ~/.dotfiles 2>&1 | tail -30

# Last successful rebuild
ls -la /run/current-system
stat /run/current-system | grep Modify
```

**Common build failures:**
- `attribute not found` → Check flake inputs, module imports
- `hash mismatch` → `nix-store --repair-path` or update flake lock
- `out of disk space` → Run garbage collection first
- `infinite recursion` → Circular module imports, check `imports = [...]`

### 5. Systemd Services Deep Dive
```bash
# All failed units with details
systemctl --failed --no-pager
systemctl --user --failed --no-pager

# Check specific service
systemctl status <service> --no-pager -l
journalctl -u <service> --no-pager -n 50

# Services that restarted too many times
systemctl list-units --state=failed --no-pager

# Check for crash-looping services
systemctl show <service> -p NRestarts
```

### 6. Network & DNS
```bash
# DNS resolution
resolvectl status 2>/dev/null || cat /etc/resolv.conf
dig google.com +short 2>/dev/null || nslookup google.com

# Network interfaces
ip addr show | grep -E "^[0-9]|inet "

# Active connections
ss -tlnp | head -20

# Firewall rules
sudo iptables -L -n 2>/dev/null | head -20
sudo nft list ruleset 2>/dev/null | head -20
```

### 7. Display / Hyprland (Wayland)
```bash
# Hyprland version & status
hyprctl version 2>/dev/null
hyprctl monitors 2>/dev/null

# GPU info
lspci | grep -i vga
cat /proc/driver/nvidia/version 2>/dev/null || echo "No NVIDIA driver loaded"

# Wayland session
echo $XDG_SESSION_TYPE
echo $WAYLAND_DISPLAY

# Recent Hyprland crashes
journalctl --user -u hyprland 2>/dev/null | tail -20
cat /tmp/hypr/*/hyprland.log 2>/dev/null | tail -30
```

### 8. Hardware Sensors
```bash
# CPU temperature
cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | awk '{printf "%.1f°C\n", $1/1000}'

# Battery (laptops)
cat /sys/class/power_supply/BAT*/capacity 2>/dev/null
cat /sys/class/power_supply/BAT*/status 2>/dev/null

# Fan speeds (if available)
sensors 2>/dev/null | grep -i fan
```

## Common NixOS Issues & Fixes

### "command not found" after rebuild
The package might be in a different output or need a wrapper:
```bash
# Find which package provides a command
nix-locate --whole-name bin/<command>
# Or search
nix search nixpkgs <term>
```

### Setuid wrappers not working
NixOS puts setuid binaries in `/run/wrappers/bin`, not the usual places:
```bash
ls /run/wrappers/bin/
# Common: sudo, ping, mount, umount, su, passwd
```

### Home Manager conflicts
```bash
# Check HM generation
home-manager generations | head -5

# Force rebuild
home-manager switch --flake ~/.dotfiles -b backup

# Check for conflicts
home-manager switch --flake ~/.dotfiles 2>&1 | grep -i conflict
```

### Nix daemon issues
```bash
systemctl status nix-daemon
# Restart if stuck
sudo systemctl restart nix-daemon
```

### Boot loader issues
```bash
# Check boot entries
bootctl list 2>/dev/null || ls /boot/loader/entries/

# Verify current boot
cat /proc/cmdline

# Check GRUB (if using GRUB)
cat /boot/grub/grub.cfg 2>/dev/null | grep menuentry | head -10
```

## Proactive Health Report

Generate a summary like:
```
🏥 NixOS Health Report — 2026-01-29

✅ Disk: 63% used (91GB free)
✅ Memory: 8.2/16GB used
✅ Systemd: No failed units
✅ Nix Store: 45GB, 1,234 paths
⚠️  Generations: 47 (consider cleanup — keep last 10)
⚠️  Last rebuild: 3 days ago
❌ Hey Clever: disabled (needs agenix secret deployment)

Recommendations:
1. Run `sudo nix-collect-garbage --delete-older-than 7d` to free ~8GB
2. Run `sudo nixos-rebuild switch --flake ~/.dotfiles` to deploy pending changes
3. Re-enable hey-bot after rebuild
```

## Integration Notes

- Works best with elevated exec permissions (sudo access)
- Designed for Flake-based NixOS setups with Home Manager
- Can be scheduled via heartbeat for periodic health checks
- Pairs well with the Morning Brief skill for daily status
- Store results in `memory/YYYY-MM-DD.md` for trend tracking

## Tags
`#nixos` `#system-health` `#diagnostics` `#troubleshooting` `#devops`
