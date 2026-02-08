{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/tmux-editor-toggle;

  tmux-editor-toggle = pkgs.writeShellScriptBin "tmux-editor-toggle" ''
    ${script}
  '';
in
{
  home.packages = [ tmux-editor-toggle ];
}
