{ config, ... }:
{
  home.activation.copyKarabinerConfig = config.lib.dag.entryAfter [ "writeBoundary" ] ''
    mkdir -p "$HOME/.config/karabiner"
    cp -f ${../../../.config/karabiner/karabiner.json} "$HOME/.config/karabiner/karabiner.json"
    chmod 644 "$HOME/.config/karabiner/karabiner.json"
  '';
}
