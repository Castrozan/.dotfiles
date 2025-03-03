let
  unstable =
    import
      (builtins.fetchTarball {
        url = "https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz";
        sha256 = "0wr8pnx2bkr88vxv3aqa9y9vrcixicm2vahws7i2kvcpy8mnb4sr";
      })
      {
        config = {
          allowUnfree = true;
        };
        system = "x86_64-linux";
      };
in
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
