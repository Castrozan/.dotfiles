let
  personal_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDXjYtc1kccaHnEeCnLfn5jB+3K8ULqIIsFoq+4pc+fX";
in
{
  "id_ed25519_phone.age".publicKeys = [ personal_key ];
  "clawdbot-gateway-token.age".publicKeys = [ personal_key ];
}
