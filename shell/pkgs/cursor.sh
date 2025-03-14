#!/usr/bin/env bash

. "./shell/src/print.sh"
. "./shell/src/is_desktop_environment.sh"
. "./shell/src/is_installed.sh"

# Install Cursor AppImage
install_cursor() {
    local version="0.46.11"
    local app_dir="$HOME/.local/share/applications"
    local bin_dir="$HOME/.local/bin"
    local cursor_dir="$HOME/.local/share/cursor"
    
    # Create necessary directories
    mkdir -p "$cursor_dir"
    mkdir -p "$app_dir"
    mkdir -p "$bin_dir"
    
    # Download AppImage
    local base_url="https://anysphere-binaries.s3.us-east-1.amazonaws.com/production/client/linux/x64/appimage"
    local file_name="Cursor-${version}-ae378be9dc2f5f1a6a1a220c6e25f9f03c8d4e19.deb.glibc2.25-x86_64.AppImage"
    curl -L "${base_url}/${file_name}" -o "$cursor_dir/cursor.AppImage"
    chmod +x "$cursor_dir/cursor.AppImage"
    
    # Create desktop entry
    cat > "$app_dir/cursor.desktop" << EOF
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
}

if is_desktop_environment; then
    # Check if Cursor is installed
    if is_installed "cursor" "appimage" >/dev/null 2>&1; then
        print "Cursor already installed" "$_YELLOW"
    else
        install_cursor
    fi
fi
