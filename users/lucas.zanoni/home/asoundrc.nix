{ ... }:
{
  # Ensure ALSA libraries are available for any speech/voice extensions.
  # See home/modules/vscode/dependencies/vscode-speech.nix for more details.
  home.file.".asoundrc".text = ''
    defaults.pcm.card 0
    defaults.ctl.card 0
  '';
}
