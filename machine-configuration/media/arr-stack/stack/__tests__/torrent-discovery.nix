{
  helpers,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  composeText = builtins.readFile ../docker-compose.yml;
  stablePublicDnsAnchor = "x-stable-public-dns: &stable-public-dns\n  - 1.1.1.1\n  - 8.8.8.8";
  prowlarrUsesStablePublicDns =
    lib.hasInfix stablePublicDnsAnchor composeText
    && lib.hasInfix "container_name: arr-prowlarr\n    restart: \"no\"\n    networks:\n      - arrnet\n    dns: *stable-public-dns" composeText;
in
{
  chise-arr-stack-prowlarr-uses-stable-public-dns =
    mkEvalCheck "chise-arr-stack-prowlarr-uses-stable-public-dns" prowlarrUsesStablePublicDns
      "Prowlarr must bypass Docker's unusable MagicDNS upstream so every enabled torrent indexer remains searchable";
}
