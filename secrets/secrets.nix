let
  personal_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDXjYtc1kccaHnEeCnLfn5jB+3K8ULqIIsFoq+4pc+fX";
in
{
  "id_ed25519_phone.age".publicKeys = [ personal_key ];
  "openclaw-gateway-token.age".publicKeys = [ personal_key ];
  "telegram-bot-token.age".publicKeys = [ personal_key ];
  "nvidia-api-key.age".publicKeys = [ personal_key ];
  "id_ed25519_workpc.age".publicKeys = [ personal_key ];
  "grid-token-robson.age".publicKeys = [ personal_key ];
  "grid-token-clever.age".publicKeys = [ personal_key ];
  "brave-api-key.age".publicKeys = [ personal_key ];
  "tavily-api-key.age".publicKeys = [ personal_key ];
  "grid-hosts.age".publicKeys = [ personal_key ];
  "ssh-hosts.age".publicKeys = [ personal_key ];
  "telegram-ids.age".publicKeys = [ personal_key ];
}
