{ unstable, ... }:
{
  environment.systemPackages = with unstable; [
    # Cursor and its dependencies
    code-cursor
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

    brave
  ];
}
