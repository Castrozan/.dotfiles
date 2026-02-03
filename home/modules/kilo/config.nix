# Kilo Code configuration
# Config file at ~/.kilocode/settings/settings.json contains kilocodeToken
{ config, lib, pkgs, ... }:
let
  # Check if running on NixOS (has agenix secrets)
  isNixOS = builtins.pathExists /etc/NIXOS;
  
  # Setup script that configures Kilo Code with the API token from agenix
  setupKilo = pkgs.writeShellScriptBin "setup-kilo" ''
    CONFIG_DIR="$HOME/.kilocode/settings"
    CONFIG_FILE="$CONFIG_DIR/settings.json"
    SECRET_FILE="/run/agenix/kilo-api-key"
    
    # Create config directory
    mkdir -p "$CONFIG_DIR"
    
    if [ -f "$SECRET_FILE" ]; then
      TOKEN=$(cat "$SECRET_FILE")
      
      # Create or update config file
      if [ -f "$CONFIG_FILE" ]; then
        # Update existing config with jq
        ${pkgs.jq}/bin/jq --arg token "$TOKEN" '.kilocodeToken = $token' "$CONFIG_FILE" > "$CONFIG_FILE.tmp"
        mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
      else
        # Create new config
        echo "{\"kilocodeToken\": \"$TOKEN\"}" | ${pkgs.jq}/bin/jq '.' > "$CONFIG_FILE"
      fi
      
      chmod 600 "$CONFIG_FILE"
      echo "Kilo Code configured with API token"
    else
      echo "Warning: Kilo API key not found at $SECRET_FILE"
      echo "Run 'sudo nixos-rebuild switch' to decrypt secrets"
    fi
  '';
in
{
  home.packages = [ setupKilo ];
  
  # Create the config directory
  home.file.".kilocode/.keep".text = "";
  
  # Activation script to set up config on rebuild
  home.activation.setupKiloConfig = lib.mkIf isNixOS (
    lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${setupKilo}/bin/setup-kilo
    ''
  );
}
