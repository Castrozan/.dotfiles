# Clipboard Manager Alternatives for GNOME

## Why Replace Clipse on GNOME?

Clipse relies on `wl-paste --watch` which requires wlroots data-control protocol. GNOME doesn't support this protocol.

## GPaste (Recommended for GNOME)

Native GNOME clipboard manager with full Wayland support.

### Installation (NixOS/home-manager)

```nix
# In home.nix or a module
{ pkgs, ... }:
{
  home.packages = with pkgs; [
    gnome-shell-extensions
    gnomeExtensions.gpaste
  ];

  # Or use the service
  services.gpaste.enable = true;
}
```

### Features
- Native GNOME integration
- Keyboard shortcut: Ctrl+Alt+H (default)
- Image support
- History persistence
- GNOME Shell extension for quick access

### Keybinding Setup

```nix
# In dconf.nix
"org/gnome/shell/keybindings" = {
  toggle-gpaste = ["<Super>v"];
};
```

## CopyQ

Cross-platform clipboard manager with GUI.

```nix
{ pkgs, ... }:
{
  home.packages = [ pkgs.copyq ];

  # Autostart
  xdg.configFile."autostart/copyq.desktop".text = ''
    [Desktop Entry]
    Name=CopyQ
    Exec=copyq
    Type=Application
    X-GNOME-Autostart-enabled=true
  '';
}
```

## Clipman (for wlroots only)

Only works on Sway/Hyprland, not GNOME.

```nix
{ pkgs, ... }:
{
  home.packages = with pkgs; [
    clipman
    wl-clipboard
  ];
}
```

## Migration from Clipse

### Export Clipse History

```bash
# Clipse stores history in JSON
cat ~/.config/clipse/clipboard_history.json | jq '.clipboardHistory[].value'
```

### Import to GPaste

```bash
# GPaste CLI
gpaste-client add "text to add"

# Or import from file
while read -r line; do
  gpaste-client add "$line"
done < exported_history.txt
```

## Comparison

| Feature | Clipse | GPaste | CopyQ |
|---------|--------|--------|-------|
| GNOME Native | No | Yes | No |
| Wayland | wlroots only | Full | Partial |
| TUI | Yes | No | No |
| GUI | No | Extension | Yes |
| Images | Yes | Yes | Yes |
| Keyboard-driven | Excellent | Good | Good |
