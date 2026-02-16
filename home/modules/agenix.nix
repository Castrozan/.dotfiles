{
  inputs,
  config,
  lib,
  ...
}:
let
  secretsDirectory = "${config.home.homeDirectory}/.secrets";

  makeSecret = name: {
    file = ../../secrets/${name}.age;
    path = "${secretsDirectory}/${name}";
  };

  secretsWithEnvironmentVariables = {
    "betha-email" = "BETHA_EMAIL";
    "betha-password" = "BETHA_PASSWORD";
    "jira-token" = "JIRA_TOKEN";
    "elastic-password" = "ELASTIC_PASSWORD";
    "grafana-password" = "GRAFANA_PASSWORD";
    "metabase-api-key" = "METABASE_API_KEY";
    "wiki-token" = "WIKI_TOKEN";
  };

  secretsWithoutEnvironmentVariables = [
    "x-username"
    "x-email"
    "x-password"
  ];

  allSecretNames =
    (lib.attrNames secretsWithEnvironmentVariables) ++ secretsWithoutEnvironmentVariables;

  exportLines = lib.concatStringsSep "\n" (
    lib.mapAttrsToList (
      secretName: envVariable: ''${envVariable}="$(cat ${secretsDirectory}/${secretName} 2>/dev/null)"''
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
  imports = [ inputs.agenix.homeManagerModules.default ];

  age = {
    identityPaths = [ "${config.home.homeDirectory}/.ssh/id_ed25519" ];
    secrets = builtins.listToAttrs (
      map (name: {
        inherit name;
        value = makeSecret name;
      }) allSecretNames
    );
  };

  home.file.".secrets/source-secrets.sh" = {
    text = sourceSecretsScriptContent;
    executable = true;
  };
}
