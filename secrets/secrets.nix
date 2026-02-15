let
  personal_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDXjYtc1kccaHnEeCnLfn5jB+3K8ULqIIsFoq+4pc+fX";
  workpc_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPdOdWOmB7IhmU70+VwgUJ40MHCOwhhrDBn6rq/Fskq/";
  all_keys = [
    personal_key
    workpc_key
  ];
in
{
  "id_ed25519_phone.age".publicKeys = all_keys;
  "openclaw-gateway-token.age".publicKeys = all_keys;
  "telegram-bot-token.age".publicKeys = all_keys;
  "nvidia-api-key.age".publicKeys = all_keys;
  "id_ed25519_workpc.age".publicKeys = all_keys;
  "grid-token-robson.age".publicKeys = all_keys;
  "grid-token-clever.age".publicKeys = all_keys;
  "brave-api-key.age".publicKeys = all_keys;
  "tavily-api-key.age".publicKeys = all_keys;
  "grid-hosts.age".publicKeys = all_keys;
  "ssh-hosts.age".publicKeys = all_keys;
  "telegram-ids.age".publicKeys = all_keys;
  "telegram-bot-token-clever.age".publicKeys = all_keys;
  "telegram-bot-token-robson.age".publicKeys = all_keys;
  "telegram-bot-token-jenny.age".publicKeys = all_keys;
  "telegram-bot-token-monster.age".publicKeys = all_keys;
  "telegram-bot-token-golden.age".publicKeys = all_keys;
  "telegram-bot-token-silver.age".publicKeys = all_keys;
  "telegram-bot-token-jarvis.age".publicKeys = all_keys;
  "deepgram-api-key.age".publicKeys = all_keys;
  "openai-api-key.age".publicKeys = all_keys;
  "betha-credentials.age".publicKeys = all_keys;
  "skill-atendimento-env.age".publicKeys = all_keys;
}
