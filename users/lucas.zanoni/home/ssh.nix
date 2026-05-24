{ lib, pkgs, ... }:
let
  sshHostsSecretExists = builtins.pathExists ../../../secrets/infrastructure/ssh-hosts.age;

  privateConfigRoot = ../../../private-config;
  workpcPrivateConfigExists = builtins.pathExists privateConfigRoot;

  generateScript = pkgs.writeShellApplication {
    name = "generate-private-ssh-config";
    runtimeInputs = [ pkgs.coreutils ];
    text = ''
      export SSH_HOSTS_FILE="/run/agenix/ssh-hosts"
      exec ${pkgs.bash}/bin/bash ${./scripts/generate-private-ssh-config.sh}
    '';
  };
in
{
  imports = lib.optionals workpcPrivateConfigExists [
    "${privateConfigRoot}/machines/workpc/ssh-gitlab.nix"
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
      run ${generateScript}/bin/generate-private-ssh-config
    ''
  );
}
