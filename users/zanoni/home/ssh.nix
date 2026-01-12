{ lib, ... }:
let
  phoneSecretExists = builtins.pathExists ../../../secrets/id_ed25519_phone.age;
  sshKeys = import ../ssh-keys.nix;
in
{
  programs.ssh = {
    enable = true;
    enableDefaultConfig = false;

    matchBlocks = {
      "*" = { };
    } // lib.optionalAttrs phoneSecretExists {
      "phone" = {
        hostname = "REDACTED_IP";
        user = "u0_a431";
        port = 8022; # Termux uses port 8022
        identityFile = "/run/agenix/id_ed25519_phone";
      };
      "phone-remote" = {
        hostname = "REDACTED_IP"; # Phone's Tailscale IP
        user = "u0_a431";
        port = 8022;
        identityFile = "/run/agenix/id_ed25519_phone";
      };
    };
  };

  home.file.".ssh/known_hosts_phone" = {
    text = builtins.concatStringsSep "\n" sshKeys.knownHosts + "\n";
  };

  home.activation.mergeKnownHosts = ''
    if [ -f "$HOME/.ssh/known_hosts_phone" ] && [ -s "$HOME/.ssh/known_hosts_phone" ]; then
      grep -v '^#' "$HOME/.ssh/known_hosts_phone" | grep -v '^$' >> "$HOME/.ssh/known_hosts" 2>/dev/null || true
      sort -u "$HOME/.ssh/known_hosts" -o "$HOME/.ssh/known_hosts" 2>/dev/null || true
    fi
  '';
}
