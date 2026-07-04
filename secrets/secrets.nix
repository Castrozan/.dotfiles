let
  chise_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDXjYtc1kccaHnEeCnLfn5jB+3K8ULqIIsFoq+4pc+fX";
  jojo_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPdOdWOmB7IhmU70+VwgUJ40MHCOwhhrDBn6rq/Fskq/";
  rin_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICpNZt8hGVbToPSE0nqVFXsGSM3Zae2tAH/lmVN5rD1x";
  kira_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJw+IAmg/Vwv7U3BKyKl5fE+VidKx3ZPp8fkWJTy4jNG";
  all_keys = [
    chise_key
    jojo_key
    rin_key
    kira_key
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

  "discord-channels/discord-channels-monster.age".publicKeys = all_keys;

  "api-keys/brave-api-key.age".publicKeys = all_keys;
  "api-keys/figma-personal-access-token-kira.age".publicKeys = all_keys;
  "api-keys/figma-personal-access-token-rin.age".publicKeys = all_keys;
  "api-keys/deepgram-api-key.age".publicKeys = all_keys;
  "api-keys/gemini-api-key.age".publicKeys = all_keys;
  "api-keys/nvidia-api-key.age".publicKeys = all_keys;
  "api-keys/openai-api-key.age".publicKeys = all_keys;
  "api-keys/tavily-api-key.age".publicKeys = all_keys;
  "api-keys/grid-token-robson.age".publicKeys = all_keys;
  "api-keys/grid-token-clever.age".publicKeys = all_keys;
  "api-keys/todoist-api-token.age".publicKeys = all_keys;

  "credentials/jira-api-token.age".publicKeys = all_keys;
  "credentials/glab-token.age".publicKeys = all_keys;
  "credentials/x-username.age".publicKeys = all_keys;
  "credentials/x-email.age".publicKeys = all_keys;
  "credentials/x-password.age".publicKeys = all_keys;
  "credentials/x-cookies.age".publicKeys = all_keys;
  "credentials/obsidian-headless-auth-token.age".publicKeys = all_keys;
  "credentials/obsidian-headless-sync-config.age".publicKeys = all_keys;
  "credentials/viu-auth.age".publicKeys = all_keys;
  "credentials/home-assistant-token.age".publicKeys = all_keys;
  "credentials/samaritano-tracker.age".publicKeys = all_keys;
  "credentials/google-totp-secret.age".publicKeys = all_keys;
  "credentials/gcp-usage-uploader-key.age".publicKeys = all_keys;

  "infrastructure/id_ed25519_phone.age".publicKeys = all_keys;
  "infrastructure/id_ed25519_jojo.age".publicKeys = all_keys;
  "infrastructure/grid-hosts.age".publicKeys = all_keys;
  "infrastructure/ssh-hosts.age".publicKeys = all_keys;
  "infrastructure/gpg-private-key.age".publicKeys = all_keys;
  "infrastructure/wifi-psk-zanoni.age".publicKeys = all_keys;
  "infrastructure/telegram-ids.age".publicKeys = all_keys;
  "infrastructure/jarvis-session-connector-credentials.age".publicKeys = all_keys;
  "infrastructure/kira-session-connector-credentials.age".publicKeys = all_keys;
  "infrastructure/rin-session-connector-credentials.age".publicKeys = all_keys;
}
