{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/quickshell-osd-send;

  quickshell-osd-send = pkgs.writeShellScriptBin "quickshell-osd-send" ''
    export PATH="${pkgs.socat}/bin:$PATH"
    ${script}
  '';
in
{
  home.packages = [ quickshell-osd-send ];
}
