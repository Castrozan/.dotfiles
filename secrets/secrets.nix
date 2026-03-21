let
  personal_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDXjYtc1kccaHnEeCnLfn5jB+3K8ULqIIsFoq+4pc+fX";
  workpc_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPdOdWOmB7IhmU70+VwgUJ40MHCOwhhrDBn6rq/Fskq/";
  all_keys = [
    personal_key
    workpc_key
  ];
in
{
  "bot-tokens/telegram-bot-token.age".publicKeys = all_keys;
  "bot-tokens/telegram-bot-token-jarvis.age".publicKeys = all_keys;
  "bot-tokens/telegram-bot-token-clever.age".publicKeys = all_keys;
  "bot-tokens/telegram-bot-token-golden.age".publicKeys = all_keys;
  "bot-tokens/telegram-bot-token-robson.age".publicKeys = all_keys;
  "bot-tokens/telegram-bot-token-jenny.age".publicKeys = all_keys;
  "bot-tokens/telegram-bot-token-monster.age".publicKeys = all_keys;
  "bot-tokens/telegram-bot-token-silver.age".publicKeys = all_keys;
  "bot-tokens/discord-bot-token-jarvis.age".publicKeys = all_keys;
  "bot-tokens/discord-bot-token-clever.age".publicKeys = all_keys;
  "bot-tokens/discord-bot-token-golden.age".publicKeys = all_keys;
  "bot-tokens/discord-bot-token-robson.age".publicKeys = all_keys;
  "bot-tokens/discord-bot-token-jenny.age".publicKeys = all_keys;
  "bot-tokens/discord-bot-token-monster.age".publicKeys = all_keys;
  "bot-tokens/discord-bot-token-silver.age".publicKeys = all_keys;

  "bot-tokens/discord-bot-token-claude.age".publicKeys = all_keys;

  "api-keys/brave-api-key.age".publicKeys = all_keys;
  "api-keys/deepgram-api-key.age".publicKeys = all_keys;
  "api-keys/gemini-api-key.age".publicKeys = all_keys;
  "api-keys/nvidia-api-key.age".publicKeys = all_keys;
  "api-keys/openai-api-key.age".publicKeys = all_keys;
  "api-keys/tavily-api-key.age".publicKeys = all_keys;
  "api-keys/openclaw-gateway-token.age".publicKeys = all_keys;
  "api-keys/metabase-api-key.age".publicKeys = all_keys;
  "api-keys/grid-token-robson.age".publicKeys = all_keys;
  "api-keys/grid-token-clever.age".publicKeys = all_keys;

  "credentials/betha-email.age".publicKeys = all_keys;
  "credentials/betha-password.age".publicKeys = all_keys;
  "credentials/elastic-password.age".publicKeys = all_keys;
  "credentials/grafana-password.age".publicKeys = all_keys;
  "credentials/jira-token.age".publicKeys = all_keys;
  "credentials/wiki-token.age".publicKeys = all_keys;
  "credentials/x-username.age".publicKeys = all_keys;
  "credentials/x-email.age".publicKeys = all_keys;
  "credentials/x-password.age".publicKeys = all_keys;
  "credentials/obsidian-headless-auth-token.age".publicKeys = all_keys;
  "credentials/obsidian-headless-sync-config.age".publicKeys = all_keys;
  "credentials/viu-auth.age".publicKeys = all_keys;
  "credentials/home-assistant-token.age".publicKeys = all_keys;
  "credentials/google-totp-secret.age".publicKeys = all_keys;

  "infrastructure/id_ed25519_phone.age".publicKeys = all_keys;
  "infrastructure/id_ed25519_workpc.age".publicKeys = all_keys;
  "infrastructure/grid-hosts.age".publicKeys = all_keys;
  "infrastructure/ssh-hosts.age".publicKeys = all_keys;
  "infrastructure/gpg-private-key.age".publicKeys = all_keys;
  "infrastructure/wifi-psk-zanoni.age".publicKeys = all_keys;
  "infrastructure/telegram-ids.age".publicKeys = all_keys;
}
