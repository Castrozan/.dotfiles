{ pkgs, lib, ... }:
{
  home.activation.seedHerdrConfigAsMutableFile = {
    after = [ "writeBoundary" ];
    before = [ ];
    data = ''
      export HERDR_CONFIG="$HOME/.config/herdr/config.toml"
      export HERDR_NIX_SOURCE="$HOME/.config/herdr/config.toml.nix-source"
      ${lib.optionalString pkgs.stdenv.hostPlatform.isLinux "export HERDR_RUNTIME_OWNS_ACCENT=1"}
      ${pkgs.python3}/bin/python3 ${./seed-herdr-config-mutable.py}
    '';
  };
}
