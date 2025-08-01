# Default directories for the shell

# Create repo directory if it doesn't exist
if test ! -d "$HOME/repo"
    mkdir -p "$HOME/repo"
end

# Create satc directory if it doesn't exist
if test ! -d "$HOME/repo/satc"
    mkdir -p "$HOME/repo/satc"
end

# Create fonts directory if it doesn't exist
if test ! -d "$HOME/.local/share/fonts"
    mkdir -p "$HOME/.local/share/fonts"
end
