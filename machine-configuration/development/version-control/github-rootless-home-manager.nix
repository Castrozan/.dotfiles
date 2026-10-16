{
  config,
  inputs,
  lib,
  pkgs,
  ...
}:
{
  imports = [
    inputs.agenix.homeManagerModules.default
    ./github-home-manager.nix
  ];

  age = {
    identityPaths = lib.mkDefault [ "${config.home.homeDirectory}/.config/age/keys.txt" ];
    secretsDir = "${config.xdg.stateHome}/agenix";
    secretsMountPoint = "${config.xdg.stateHome}/agenix.d";
    secrets =
      lib.optionalAttrs (builtins.pathExists ../../../secrets/credentials/github-com-token.age)
        {
          "credentials/github-com-token" = {
            file = ../../../secrets/credentials/github-com-token.age;
            path = "${config.home.homeDirectory}/.secrets/github-com-token";
            mode = "0400";
          };
        };
  };

  home.activation.mountDotGithubCredential = lib.mkIf (config.age.secrets != { }) (
    lib.hm.dag.entryBetween [ "setupGithubAuthentication" ] [ "writeBoundary" ] ''
      run ${lib.escapeShellArgs config.systemd.user.services.agenix.Service.ExecStart}
    ''
  );

  home.activation.setupDotGithubHttps = lib.hm.dag.entryAfter [ "setupGithubAuthentication" ] ''
    run ${pkgs.gh}/bin/gh config set git_protocol https --host github.com
  '';

  programs.git.settings.credential."https://github.com".helper = [
    ""
    "!${pkgs.gh}/bin/gh auth git-credential"
  ];
}
