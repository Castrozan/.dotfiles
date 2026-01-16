# RSVP speed reader script
{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/speed-read;
in
let
  speed-read = pkgs.writeShellScriptBin "speed-read" ''
    export PATH="${pkgs.bc}/bin:${pkgs.coreutils}/bin:${pkgs.gnused}/bin:$PATH"
    ${script}
  '';
in
{
  home.packages = [ speed-read ];
}
