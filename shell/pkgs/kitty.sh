#!/bin/sh

# Check if kitty is installed
if command -v kitty >/dev/null 2>&1; then
    print "Kitty already installed" "$YELLOW"
else
    install_with_custom_script_via_curl "https://sw.kovidgoyal.net/kitty/installer.sh"

    if ask "Do you want to install kitty.desktop integration?"; then
        install_kitty_desktop_integration
    fi
fi

# Desktop integration on Linux
# If you want the kitty icon to appear in the taskbar and an entry for it to be present in the menus,
# you will need to install the kitty.desktop file.
# The details of the following procedure may need to be adjusted for your particular desktop,
# but it should work for most major desktop environments.
install_kitty_desktop_integration() {

    # Create symbolic links to add kitty and kitten to PATH (assuming ~/.local/bin is in
    # your system-wide PATH)
    ln -sf ~/.local/kitty.app/bin/kitty ~/.local/kitty.app/bin/kitten ~/.local/bin/
    # Place the kitty.desktop file somewhere it can be found by the OS
    cp ~/.local/kitty.app/share/applications/kitty.desktop ~/.local/share/applications/
    # If you want to open text files and images in kitty via your file manager also add the kitty-open.desktop file
    cp ~/.local/kitty.app/share/applications/kitty-open.desktop ~/.local/share/applications/
    # Update the paths to the kitty and its icon in the kitty desktop file(s)
    sed -i "s|Icon=kitty|Icon=$(readlink -f ~)/.local/kitty.app/share/icons/hicolor/256x256/apps/kitty.png|g" ~/.local/share/applications/kitty*.desktop
    sed -i "s|Exec=kitty|Exec=$(readlink -f ~)/.local/kitty.app/bin/kitty|g" ~/.local/share/applications/kitty*.desktop
    # Make xdg-terminal-exec (and hence desktop environments that support it use kitty)
    echo 'kitty.desktop' >~/.config/xdg-terminals.list
}
