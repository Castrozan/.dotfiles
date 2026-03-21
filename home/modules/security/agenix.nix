{
  inputs,
  config,
  lib,
  ...
}:
let
  secretsDirectory = "${config.home.homeDirectory}/.secrets";

  identityKeyPath = "${config.home.homeDirectory}/.ssh/id_ed25519";

  makeSecret = name: {
    file = ../../../secrets/${name}.age;
    path = "${secretsDirectory}/${builtins.baseNameOf name}";
  };

  secretsWithEnvironmentVariables = {
    "credentials/betha-email" = "BETHA_EMAIL";
    "credentials/betha-password" = "BETHA_PASSWORD";
    "credentials/jira-token" = "JIRA_TOKEN";
    "credentials/elastic-password" = "ELASTIC_PASSWORD";
    "credentials/grafana-password" = "GRAFANA_PASSWORD";
    "api-keys/metabase-api-key" = "METABASE_API_KEY";
    "credentials/wiki-token" = "WIKI_TOKEN";
  };

  secretsWithoutEnvironmentVariables = [
    "api-keys/brave-api-key"
    "api-keys/deepgram-api-key"
    "api-keys/gemini-api-key"
    "api-keys/nvidia-api-key"
    "api-keys/openai-api-key"
    "api-keys/openclaw-gateway-token"
    "infrastructure/telegram-ids"
    "credentials/x-username"
    "credentials/x-email"
    "credentials/x-password"
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

  allSecretNames =
    (lib.attrNames secretsWithEnvironmentVariables) ++ secretsWithoutEnvironmentVariables;

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
  imports = [ inputs.agenix.homeManagerModules.default ];

  age = {
    identityPaths = [ identityKeyPath ];
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
