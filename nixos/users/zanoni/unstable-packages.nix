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
  ];
}
