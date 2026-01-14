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

    # Create npm global directory if it doesn't exist
    mkdir -p "$HOME/.npm-global/bin"

    # Install claudemem only if not already installed
    if ! [ -x "$HOME/.npm-global/bin/claude-codemem" ]; then
      echo "Installing claudemem via npm..."
      ${npmBin} install -g claude-codemem 2>/dev/null || true
    else
      echo "claudemem is already installed."
    fi
  '';
}
