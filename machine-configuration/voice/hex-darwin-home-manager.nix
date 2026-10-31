{ lib, pkgs, ... }:
let
  hexCommand = lib.escapeShellArgs [
    (lib.getExe' pkgs.coreutils "timeout")
    "--kill-after=2s"
    "8s"
    "/Applications/Hex.app/Contents/MacOS/hex"
  ];
in
{
  # The signed 3.0.0 release exposes settings through the running app only.
  home.activation.hexSettings = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    if [ -x /Applications/Hex.app/Contents/MacOS/hex ] && ${hexCommand} status --json >/dev/null 2>&1; then
      run ${hexCommand} settings set dictation_hotkey control+option+space
      run ${hexCommand} settings set history_retention off
      run ${hexCommand} settings set sound_effects false
      run ${hexCommand} settings set recording_audio_behavior do_nothing
      run ${hexCommand} settings set release_microphone_while_idle true
      run ${hexCommand} settings set capture.enabled false
      run ${hexCommand} settings set enable_on_launch true
      run ${hexCommand} launch-at-login on
    else
      warnEcho "Hex is not responding. Open Hex, then rebuild to apply its privacy settings."
    fi
  '';
}
