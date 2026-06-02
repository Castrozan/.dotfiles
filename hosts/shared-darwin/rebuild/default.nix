{ pkgs, hostname, ... }:
let
  rebuildScriptWithResolvedFlakeHostAttribute =
    builtins.replaceStrings [ "@FLAKE_HOST_ATTRIBUTE@" ] [ hostname ]
      (builtins.readFile ./rebuild);
  rebuild = pkgs.writeShellScriptBin "rebuild" rebuildScriptWithResolvedFlakeHostAttribute;
in
{
  environment.systemPackages = [ rebuild ];
}
