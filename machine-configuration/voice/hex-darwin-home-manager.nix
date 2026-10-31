{ lib, ... }:
{
  # The signed 3.0.0 release exposes settings through the running app only.
  home.activation.hexSettings = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    if [ -x /Applications/Hex.app/Contents/MacOS/hex ] && /Applications/Hex.app/Contents/MacOS/hex status --json >/dev/null 2>&1; then
      run /Applications/Hex.app/Contents/MacOS/hex settings set history_retention off
      run /Applications/Hex.app/Contents/MacOS/hex settings set sound_effects false
      run /Applications/Hex.app/Contents/MacOS/hex settings set recording_audio_behavior do_nothing
      run /Applications/Hex.app/Contents/MacOS/hex settings set release_microphone_while_idle true
      run /Applications/Hex.app/Contents/MacOS/hex settings set capture.enabled false
    else
      warnEcho "Open Hex once, then rebuild to apply its privacy settings."
    fi
  '';
}
