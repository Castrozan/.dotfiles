let
  unstable =
    import
      (builtins.fetchTarball {
        url = "https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz";
        sha256 = "0aa89pl1xs0kri9ixxg488n7riqi5n9ys89xqc0immyqshqc1d7f";
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
