# claudemem - memory/context persistence for Claude Code
# https://github.com/anthropics/claude-codemem
{ pkgs, lib, ... }:
let
  npmBin = "${pkgs.nodejs}/bin/npm";
in
{
  home.packages = with pkgs; [ nodejs ];

  # Ensure npm global bin directory is in PATH
  home.sessionPath = [ "$HOME/.npm-global/bin" ];

  # Configure npm to use a user-local directory for global installs
  home.sessionVariables = {
    NPM_CONFIG_PREFIX = "$HOME/.npm-global";
  };

  # Install claudemem globally via npm on activation
  home.activation.installClaudemem = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    export PATH="${pkgs.nodejs}/bin:$PATH"
    export NPM_CONFIG_PREFIX="$HOME/.npm-global"
    mkdir -p "$HOME/.npm-global/bin"
    if [ ! -x "$HOME/.npm-global/bin/claude-codemem" ]; then
      ${npmBin} install -g claude-codemem > /dev/null 2>&1 || true
    fi
  '';
}
