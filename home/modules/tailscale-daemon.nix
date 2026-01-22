# Reminder module for tailscale daemon on non-NixOS systems
# The daemon must be installed via the OS package manager since it needs root
_: {
  home.activation.checkTailscaleDaemon = {
    after = [ "writeBoundary" ];
    before = [ ];
    data = ''
      if ! command -v tailscaled >/dev/null 2>&1 && \
         [ ! -x "$HOME/.nix-profile/bin/tailscaled" ] && \
         [ ! -x "/usr/sbin/tailscaled" ]; then
        echo "WARNING: tailscaled not found. Install via:"
        echo "  curl -fsSL https://tailscale.com/install.sh | sh"
      fi
    '';
  };
}
