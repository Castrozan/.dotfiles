{ pkgs, ... }:
let
  mediaScripts = ./scripts;
  generateAgentVoiceNote = pkgs.writeShellScriptBin "clawde-agent-voice-note" ''
    exec ${pkgs.python312}/bin/python3 ${mediaScripts}/generate_agent_voice_note.py "$@"
  '';
in
{
  home.packages = [ generateAgentVoiceNote ];
}
