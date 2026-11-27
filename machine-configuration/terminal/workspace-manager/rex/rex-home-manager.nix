{ pkgs, lib, ... }:
let
  rexBundledCommandLine = "/Applications/Rex.app/Contents/Helpers/Rex Server.rex/Contents/MacOS/rex";
  rexCommandLine = pkgs.writeShellScriptBin "rex" ''
    exec "${rexBundledCommandLine}" "$@"
  '';
in
{
  home.packages = [ rexCommandLine ];

  xdg.configFile."rex/init.lua".source = ./program-configuration/init.lua;

  home.activation.reloadRexConfiguration = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
    if [ -x "${rexBundledCommandLine}" ]; then
      "${rexBundledCommandLine}" config reload >/dev/null 2>&1 || true
    fi
  '';
}
