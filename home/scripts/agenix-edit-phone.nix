{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/agenix-edit-phone;
in
let
  agenix-edit-phone = pkgs.writeShellScriptBin "agenix-edit-phone" ''
    ${script}
  '';
in
{
  home.packages = [ agenix-edit-phone ];
}
