#!/usr/bin/env bash

. "./shell/src/print.sh"
. "./shell/src/is_desktop_environment.sh"
. "./shell/src/is_installed.sh"

# Install Cursor AppImage
install_cursor() {
    local app_dir="$HOME/.local/share/applications"
    local bin_dir="$HOME/.local/bin"
    local cursor_dir="$HOME/.local/share/cursor"
    local icons_dir="$HOME/.local/share/icons/hicolor/256x256/apps"

    # Create necessary directories
    mkdir -p "$cursor_dir"
    mkdir -p "$app_dir"
    mkdir -p "$bin_dir"
    mkdir -p "$icons_dir"

    # Download AppImage
    local base_url="https://downloads.cursor.com/production/1d623c4cc1d3bb6e0fe4f1d5434b47b958b05876/linux/x64/Cursor-0.48.7-x86_64.AppImage"
    curl -L "${base_url}" -o "$cursor_dir/cursor.AppImage"
    chmod +x "$cursor_dir/cursor.AppImage"

    # Download icon
    curl -L "https://raw.githubusercontent.com/getcursor/cursor/main/apps/desktop/resources/icon.png" -o "$icons_dir/cursor.png"

    # Create desktop entry
    cat >"$app_dir/cursor.desktop" <<EOF
[Desktop Entry]
Name=Cursor
Exec=$cursor_dir/cursor.AppImage
Icon=cursor
Type=Application
Categories=Development;IDE;
Comment=AI-first code editor
EOF

    # Create symbolic link to make cursor available in PATH
    ln -sf "$cursor_dir/cursor.AppImage" "$bin_dir/cursor"

    # Update icon cache
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$app_dir"
    fi

    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor"
    fi
}

if is_desktop_environment; then
    # Check if Cursor is installed
    if is_installed "cursor" "appimage" >/dev/null 2>&1; then
        print "Cursor already installed" "$_YELLOW"
    else
        install_cursor
    fi
fi
