{ lib, ... }:
{
  home.activation.hexSettings = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    if [ -x /Applications/Hex.app/Contents/MacOS/hex ]; then
      run /Applications/Hex.app/Contents/MacOS/hex settings apply ${./hex-settings.json}
    fi
  '';
}
