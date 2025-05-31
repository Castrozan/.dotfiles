{ unstable, latest, ... }:
{
  # List of pkgs installed from the unstable channel
  environment.systemPackages = with unstable; [
    cargo
    rustc
    SDL2
    alsa-lib.dev
    pkg-config
    supabase-cli

    # formatting nix
    nixfmt-rfc-style

    # Tools
    clipse

    # Applications
    brave
    latest.code-cursor
  ];
}
