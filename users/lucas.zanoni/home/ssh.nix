{ lib, pkgs, ... }:
let
  sshHostsSecretExists = builtins.pathExists ../../../secrets/ssh-hosts.age;

  generateScript = pkgs.writeShellScript "generate-private-ssh-config" ''
    set -euo pipefail
    HOSTS="/run/agenix/ssh-hosts"
    CONFIG_DIR="$HOME/.ssh/config.d"
    PRIVATE_HOSTS="$CONFIG_DIR/private-hosts"

    mkdir -p "$CONFIG_DIR"

    if [ ! -f "$HOSTS" ]; then
      rm -f "$PRIVATE_HOSTS"
      exit 0
    fi

    declare -A hosts
    while IFS='=' read -r key value; do
      [ -n "$key" ] && hosts["$key"]="$value"
    done < "$HOSTS"

    {
      if [ -n "''${hosts[dellg15]:-}" ]; then
        printf 'Host dellg15\n'
        printf '    HostName %s\n' "''${hosts[dellg15]}"
        printf '    User zanoni\n'
        printf '    IdentityFile ~/.ssh/id_ed25519\n\n'
      fi
    } > "$PRIVATE_HOSTS"
  '';
in
{
  programs.ssh = {
    enable = true;
    enableDefaultConfig = false;
    includes = lib.mkIf sshHostsSecretExists [ "~/.ssh/config.d/*" ];

    matchBlocks = {
      "*" = { };
      "gitlab.com" = {
        hostname = "gitlab.services.betha.cloud";
        user = "git";
        identityFile = "~/.ssh/id_ed25519";
      };
      "gitlab.services.betha.cloud" = {
        hostname = "gitlab.services.betha.cloud";
        user = "git";
        identityFile = "~/.ssh/id_ed25519";
      };
      "github.com" = {
        hostname = "github.com";
        user = "git";
        identityFile = "~/.ssh/id_rsa";
      };
    };
  };

  home.activation.generatePrivateSshConfig = lib.mkIf sshHostsSecretExists (
    lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${generateScript}
    ''
  );
}
