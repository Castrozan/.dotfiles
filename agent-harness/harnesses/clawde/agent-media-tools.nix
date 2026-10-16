{ pkgs, ... }:
let
  mediaScripts = ./scripts;
  generateAgentVoiceNote = pkgs.writeShellScriptBin "clawde-agent-voice-note" ''
    exec ${pkgs.python312}/bin/python3 ${mediaScripts}/generate_agent_voice_note.py "$@"
  '';
  searchAgentGifs = pkgs.writeShellScriptBin "clawde-agent-gif-search" ''
    exec ${pkgs.python312}/bin/python3 ${mediaScripts}/generate_agent_gif_search.py "$@"
  '';
  readAgentAttachment = pkgs.writeShellScriptBin "clawde-agent-attachment-read" ''
    exec ${pkgs.python312}/bin/python3 ${mediaScripts}/read_agent_attachment.py "$@"
  '';
in
{
  home.packages = [
    generateAgentVoiceNote
    searchAgentGifs
    readAgentAttachment
  ];
}
