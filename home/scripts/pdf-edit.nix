{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/pdf_edit;

  pdf-edit = pkgs.writeShellScriptBin "pdf-edit" ''
    ${script}
  '';
in
{
  home.packages = [ pdf-edit ];
}
