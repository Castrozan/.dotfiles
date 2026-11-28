{
  inputs,
  config,
  lib,
  pkgs,
  hostname,
  healthCheckLib,
  ...
}:
let
  secretsDirectory = "${config.home.homeDirectory}/.secrets";

  primaryIdentityKeyPath = "${config.home.homeDirectory}/.ssh/id_ed25519";
  identityKeyPaths = [ primaryIdentityKeyPath ];

  privateConfigRoot = ../../../private-configuration;
  privateMachineSecretsModulePath = "${toString privateConfigRoot}/machines/${hostname}/secrets.nix";
  privateMachineSecretsModuleExists = builtins.pathExists privateMachineSecretsModulePath;

  makeSecret = secret: {
    inherit (secret) file;
    path = "${secretsDirectory}/${builtins.baseNameOf secret.name}";
  };

  secretsWithEnvironmentVariables = {
    "credentials/jira-api-token" = "JIRA_API_TOKEN";
    "credentials/glab-token" = "GITLAB_TOKEN";
  };

  availableSecrets = builtins.filter (secret: builtins.pathExists secret.file) (
    import ./public-secret-sources.nix
  );

  exportLines = lib.concatStringsSep "\n" (
    lib.mapAttrsToList (
      secretName: envVariable:
      ''${envVariable}="$(cat ${secretsDirectory}/${builtins.baseNameOf secretName} 2>/dev/null)"''
    ) secretsWithEnvironmentVariables
  );

  allEnvironmentVariableNames = lib.attrValues secretsWithEnvironmentVariables;

  sourceSecretsScriptContent = ''
    #!/usr/bin/env bash
    ${exportLines}
    export ${lib.concatStringsSep " " allEnvironmentVariableNames}
  '';
in
{
  imports = [
    inputs.agenix.homeManagerModules.default
    ./credentials-env-file-writer-home-manager.nix
  ]
  ++ lib.optionals privateMachineSecretsModuleExists [
    privateMachineSecretsModulePath
  ];

  age = {
    identityPaths = identityKeyPaths;
    secrets = builtins.listToAttrs (
      map (secret: {
        inherit (secret) name;
        value = makeSecret secret;
      }) availableSecrets
    );
  };

  home.file.".secrets/source-secrets.sh" = {
    text = sourceSecretsScriptContent;
    executable = true;
  };

  healthCheck.probes = map (
    secret:
    healthCheckLib.mkFileProbe {
      category = "secret";
      name = "agenix: ${secret.name}";
      path = "${secretsDirectory}/${builtins.baseNameOf secret.name}";
    }
  ) availableSecrets;

  home.activation.disableAgenixLaunchdRestartLoop = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin (
    lib.hm.dag.entryAfter [ "setupLaunchAgents" ] ''
      $DRY_RUN_CMD ${pkgs.python312}/bin/python3 ${./scripts/restart_agenix_launch_agent.py} ${lib.escapeShellArg config.home.homeDirectory}
    ''
  );
}
