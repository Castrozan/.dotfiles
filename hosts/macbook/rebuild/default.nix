{ pkgs, ... }:
let
  rebuild = pkgs.writeShellScriptBin "rebuild" (builtins.readFile ./rebuild);
in
{
  environment.systemPackages = [ rebuild ];
}
