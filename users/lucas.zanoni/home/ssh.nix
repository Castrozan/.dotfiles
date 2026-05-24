{ lib, pkgs, ... }:
let
  sshHostsSecretExists = builtins.pathExists ../../../secrets/infrastructure/ssh-hosts.age;

  workpcPrivateConfigDirectory = ../../../private-config/machines/workpc;
  workpcPrivateConfigExists = builtins.pathExists workpcPrivateConfigDirectory;

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
            printf 'Host dellg15
    '
            printf '    HostName %s
    ' "''${hosts[dellg15]}"
            printf '    User zanoni
    '
            printf '    IdentityFile ~/.ssh/id_ed25519

    '
          fi
        } > "$PRIVATE_HOSTS"
  '';
in
{
  imports = lib.optionals workpcPrivateConfigExists [
    "${workpcPrivateConfigDirectory}/ssh-gitlab.nix"
  ];

  programs.ssh = {
    enable = true;
    enableDefaultConfig = false;
    includes = lib.mkIf sshHostsSecretExists [ "~/.ssh/config.d/*" ];

    matchBlocks = {
      "*" = { };
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
