{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/mouse-poll-rate;

  mousePollRate = pkgs.writeShellScriptBin "mouse-poll-rate" ''
    export PATH="${pkgs.python3}/bin:$PATH"
    ${script}
  '';
in
{
  home.packages = [ mousePollRate ];
}
