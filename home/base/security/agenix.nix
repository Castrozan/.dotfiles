{
  inputs,
  config,
  lib,
  hostname,
  ...
}:
let
  secretsDirectory = "${config.home.homeDirectory}/.secrets";

  primaryIdentityKeyPath = "${config.home.homeDirectory}/.ssh/id_ed25519";
  hostsWithDedicatedSystemIdentity = {
    rin = "${config.home.homeDirectory}/.ssh/id_ed25519_nixos";
  };
  dedicatedSystemIdentityKeyPaths = lib.optional (
    hostsWithDedicatedSystemIdentity ? ${hostname}
  ) hostsWithDedicatedSystemIdentity.${hostname};
  identityKeyPaths = [ primaryIdentityKeyPath ] ++ dedicatedSystemIdentityKeyPaths;

  privateConfigRoot = ../../../private-config;
  privateMachineSecretsModulePath = "${toString privateConfigRoot}/machines/${hostname}/secrets.nix";
  privateMachineSecretsModuleExists = builtins.pathExists privateMachineSecretsModulePath;

  makeSecret = name: {
    file = ../../../secrets/${name}.age;
    path = "${secretsDirectory}/${builtins.baseNameOf name}";
  };

  secretsWithEnvironmentVariables = {
    "credentials/work-email" = "WORK_EMAIL";
    "credentials/work-password" = "WORK_PASSWORD";
    "credentials/jira-token" = "JIRA_TOKEN";
    "credentials/jira-api-token" = "JIRA_API_TOKEN";
    "credentials/elastic-password" = "ELASTIC_PASSWORD";
    "credentials/grafana-password" = "GRAFANA_PASSWORD";
    "api-keys/metabase-api-key" = "METABASE_API_KEY";
    "credentials/wiki-token" = "WIKI_TOKEN";
    "credentials/glab-token" = "GITLAB_TOKEN";
  };

  secretsWithoutEnvironmentVariables = [
    "api-keys/brave-api-key"
    "api-keys/deepgram-api-key"
    "api-keys/gemini-api-key"
    "api-keys/nvidia-api-key"
    "api-keys/openai-api-key"
    "infrastructure/telegram-ids"
    "infrastructure/ssh-hosts"
    "credentials/x-username"
    "credentials/x-email"
    "credentials/x-password"
    "credentials/x-cookies"
    "bot-tokens/telegram-bot-token-jarvis"
    "bot-tokens/telegram-bot-token-golden"
    "bot-tokens/telegram-bot-token-clever"
    "bot-tokens/telegram-bot-token-robson"
    "bot-tokens/telegram-bot-token-jenny"
    "bot-tokens/telegram-bot-token-monster"
    "bot-tokens/telegram-bot-token-silver"
    "bot-tokens/discord-bot-token-jarvis"
    "bot-tokens/discord-bot-token-golden"
    "bot-tokens/discord-bot-token-clever"
    "bot-tokens/discord-bot-token-robson"
    "bot-tokens/discord-bot-token-jenny"
    "bot-tokens/discord-bot-token-monster"
    "bot-tokens/discord-bot-token-silver"
    "bot-tokens/discord-bot-token-claude"
    "credentials/obsidian-headless-auth-token"
    "credentials/obsidian-headless-sync-config"
    "infrastructure/gpg-private-key"
    "credentials/viu-auth"
    "credentials/home-assistant-token"
    "credentials/google-totp-secret"
  ];

  secretFileExists = name: builtins.pathExists (../../../secrets/${name}.age);

  allSecretNames = builtins.filter secretFileExists (
    (lib.attrNames secretsWithEnvironmentVariables) ++ secretsWithoutEnvironmentVariables
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
  ]
  ++ lib.optionals privateMachineSecretsModuleExists [
    privateMachineSecretsModulePath
  ];

  age = {
    identityPaths = identityKeyPaths;
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
