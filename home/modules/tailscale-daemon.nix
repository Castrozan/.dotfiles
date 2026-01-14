# Reminder module for tailscale daemon on non-NixOS systems
# The daemon must be installed via the OS package manager since it needs root
{ ... }:
{
  home.activation.checkTailscaleDaemon = {
    after = [ "writeBoundary" ];
    before = [ ];
    data = ''
      if ! command -v tailscaled >/dev/null 2>&1; then
        echo "WARNING: tailscaled not found. Install via:"
        echo "  curl -fsSL https://tailscale.com/install.sh | sh"
      fi
    '';
  };
}
