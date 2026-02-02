{ lib, pkgs, ... }:
let
  phoneSecretExists = builtins.pathExists ../../../secrets/id_ed25519_phone.age;
  workpcSecretExists = builtins.pathExists ../../../secrets/id_ed25519_workpc.age;
  sshHostsSecretExists = builtins.pathExists ../../../secrets/ssh-hosts.age;

  phoneHostKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOWURbP41AHeoQUC4qpSriTvVKWezdpPMGg1f3Ti7gyd";
  workPcHostKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPctlyhhY3Tf6RS/qs4aMUK/cIiZFG804XJFbd0ooWP/";

  generateScript = pkgs.writeShellScript "generate-private-ssh-config" ''
    set -euo pipefail
    HOSTS="/run/agenix/ssh-hosts"
    SSH_DIR="$HOME/.ssh"
    CONFIG_DIR="$SSH_DIR/config.d"
    PRIVATE_HOSTS="$CONFIG_DIR/private-hosts"
    KNOWN_HOSTS="$SSH_DIR/known_hosts_private"

    mkdir -p "$CONFIG_DIR"

    if [ ! -f "$HOSTS" ]; then
      rm -f "$PRIVATE_HOSTS" "$KNOWN_HOSTS"
      exit 0
    fi

    # Parse key=value pairs from agenix secret
    declare -A hosts
    while IFS='=' read -r key value; do
      [ -n "$key" ] && hosts["$key"]="$value"
    done < "$HOSTS"

    # Generate SSH config for private hosts
    {
      if [ -n "''${hosts[workpc]:-}" ] && [ -f "/run/agenix/id_ed25519_workpc" ]; then
        printf 'Host workpc\n'
        printf '    HostName %s\n' "''${hosts[workpc]}"
        printf '    User lucas.zanoni\n'
        printf '    IdentityFile /run/agenix/id_ed25519_workpc\n\n'
      fi

      if [ -n "''${hosts[phone]:-}" ] && [ -f "/run/agenix/id_ed25519_phone" ]; then
        printf 'Host phone\n'
        printf '    HostName %s\n' "''${hosts[phone]}"
        printf '    User u0_a431\n'
        printf '    Port 8022\n'
        printf '    IdentityFile /run/agenix/id_ed25519_phone\n\n'
      fi
    } > "$PRIVATE_HOSTS"

    # Generate known_hosts entries
    {
      if [ -n "''${hosts[phone]:-}" ]; then
        printf '[%s]:8022 ${phoneHostKey}\n' "''${hosts[phone]}"
      fi
      if [ -n "''${hosts[workpc]:-}" ]; then
        printf '%s ${workPcHostKey}\n' "''${hosts[workpc]}"
      fi
    } > "$KNOWN_HOSTS"

    # Merge into main known_hosts
    if [ -s "$KNOWN_HOSTS" ]; then
      cat "$KNOWN_HOSTS" >> "$SSH_DIR/known_hosts" 2>/dev/null || true
      sort -u "$SSH_DIR/known_hosts" -o "$SSH_DIR/known_hosts" 2>/dev/null || true
    fi
  '';
in
{
  programs.ssh = {
    enable = true;
    enableDefaultConfig = false;
    includes = lib.mkIf sshHostsSecretExists [ "~/.ssh/config.d/*" ];

    matchBlocks."*" = { };
  };

  home.activation.generatePrivateSshConfig =
    lib.mkIf (sshHostsSecretExists && (phoneSecretExists || workpcSecretExists))
      (
        lib.hm.dag.entryAfter [ "writeBoundary" ] ''
          run ${generateScript}
        ''
      );
}
