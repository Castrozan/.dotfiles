{ pkgs, ... }:
let
  cloudflare = import ../package.nix { inherit pkgs; };
in
{
  cloudflare-cli-commands = pkgs.runCommand "cloudflare-cli-commands" { } ''
    export HOME="$TMPDIR"
    ${cloudflare}/bin/cf --version 2>&1 | grep -F '1.0.0-beta.12'
    ${cloudflare}/bin/cloudflare --version 2>&1 | grep -F '1.0.0-beta.12'
    ${cloudflare}/bin/cf cli search 'list zones' \
      | ${pkgs.jq}/bin/jq -e 'any(.[]; .command == "cf zones list")'
    touch "$out"
  '';
}
