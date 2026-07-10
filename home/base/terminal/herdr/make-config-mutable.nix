{ pkgs, ... }:
{
  home.activation.seedHerdrConfigAsMutableFile = {
    after = [ "writeBoundary" ];
    before = [ ];
    data = ''
      export HERDR_CONFIG="$HOME/.config/herdr/config.toml"
      export HERDR_NIX_SOURCE="$HOME/.config/herdr/config.toml.nix-source"
      ${pkgs.python3}/bin/python3 ${./seed-herdr-config-mutable.py}
    '';
  };
}
