{ pkgs, ... }:
let
  mediaScripts = ./scripts;
  generateAgentImage = pkgs.writeShellScriptBin "clawde-agent-image-generate" ''
    exec ${pkgs.python312}/bin/python3 ${mediaScripts}/generate_agent_image.py "$@"
  '';
  generateAgentVoiceNote = pkgs.writeShellScriptBin "clawde-agent-voice-note" ''
    exec ${pkgs.python312}/bin/python3 ${mediaScripts}/generate_agent_voice_note.py "$@"
  '';
in
{
  home.packages = [
    generateAgentImage
    generateAgentVoiceNote
  ];
}
