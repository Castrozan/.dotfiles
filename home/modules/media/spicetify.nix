{ pkgs, inputs, ... }:
let
  spicePkgs = inputs.spicetify-nix.legacyPackages.${pkgs.system};
in
{
  # Allow unfree packages (Spotify)
  nixpkgs.config.allowUnfreePredicate = pkg:
    builtins.elem (pkgs.lib.getName pkg) [ "spotify" ];

  # Import the home-manager module for spicetify-nix
  imports = [ inputs.spicetify-nix.homeManagerModules.default ];

  # Configure Spicetify
  programs.spicetify = {
    enable = true;

    # Enable extensions
    enabledExtensions = with spicePkgs.extensions; [
      adblock # Blocks Spotify ads
      shuffle # shuffle+ for better shuffle functionality
      hidePodcasts # Hide podcasts from the UI
    ];

    # Enable custom apps
    enabledCustomApps = with spicePkgs.apps; [
      lyricsPlus # Enhanced lyrics display
      betterLibrary # Better library management
    ];

    # Use Catppuccin theme (popular dark theme)
    theme = spicePkgs.themes.catppuccin;
    colorScheme = "mocha";
  };
}
