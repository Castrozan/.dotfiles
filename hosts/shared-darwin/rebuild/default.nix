{ pkgs, hostname, ... }:
let
  verifyDeployedProhibitedWordsAllowlist =
    import ../../../home/base/system/scripts/verify-deployed-prohibited-words-allowlist.nix
      {
        inherit pkgs;
      };
  rebuildScriptWithResolvedFlakeHostAttribute =
    builtins.replaceStrings
      [
        "@FLAKE_HOST_ATTRIBUTE@"
        "@verify-deployed-prohibited-words-allowlist@"
      ]
      [
        hostname
        "${verifyDeployedProhibitedWordsAllowlist}/bin/verify-deployed-prohibited-words-allowlist"
      ]
      (builtins.readFile ./rebuild);
  rebuild = pkgs.writeShellScriptBin "rebuild" rebuildScriptWithResolvedFlakeHostAttribute;
in
{
  environment.systemPackages = [ rebuild ];
}
