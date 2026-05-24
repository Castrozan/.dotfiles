{
  lib,
  pkgs,
  hostname,
  isDarwin,
  isNixOS,
  ...
}:
# hostname is required from extraSpecialArgs. Threaded by:
#   flake/outputs.nix (homeConfigurations), flake/darwin-configurations.nix (darwin).
# Adds private-config/machines/<hostname>/ssh.nix when that file exists.
let
  sshHostsSecretExists = builtins.pathExists ../../../secrets/infrastructure/ssh-hosts.age;

  privateConfigRoot = ../../../private-config;
  privateConfigExists = builtins.pathExists privateConfigRoot;
  privateSshOverridePath = "${toString privateConfigRoot}/machines/${hostname}/ssh.nix";
  privateSshOverrideExists = privateConfigExists && builtins.pathExists privateSshOverridePath;
  isWorkpcLinux = !isDarwin && !isNixOS;

  workpcGenerateScript = pkgs.writeShellApplication {
    name = "generate-private-ssh-config";
    runtimeInputs = [ pkgs.coreutils ];
    text = ''
      export SSH_HOSTS_FILE="/run/agenix/ssh-hosts"
      exec ${pkgs.bash}/bin/bash ${./scripts/generate-private-ssh-config.sh}
    '';
  };
in
{
  imports = lib.optionals privateSshOverrideExists [
    privateSshOverridePath
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

  home.activation.generatePrivateSshConfig = lib.mkIf (sshHostsSecretExists && isWorkpcLinux) (
    lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${workpcGenerateScript}/bin/generate-private-ssh-config
    ''
  );
}
