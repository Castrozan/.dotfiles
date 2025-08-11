# Description: Create a new markdown file with today's date and open it in the default editor
{ pkgs, ... }:

let
  on = pkgs.writeShellScriptBin "on" ''
    #!/usr/bin/env bash
    if [ -z "$1" ]; then
      echo "Error: A file name must be set, e.g. on \"the wonderful thing about tiggers\"."
      exit 1
    fi

    #TODO: Find why variable substitution is not working
    #file_name=$(echo "$1" | tr ' ' '-')
    #formatted_file_name=$(date "+%Y-%m-%d")_$(echo "$1" | tr ' ' '-').md
    cd "$OBSIDIAN_HOME" || exit
    touch $(date "+%Y-%m-%d")_$(echo "$1" | tr ' ' '-').md
    $EDITOR $(date "+%Y-%m-%d")_$(echo "$1" | tr ' ' '-').md
  '';

in
{
  environment.systemPackages = [ on ];
}
