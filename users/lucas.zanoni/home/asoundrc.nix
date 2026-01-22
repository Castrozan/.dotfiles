_:
{
  # Ensure ALSA libraries are available for any speech/voice extensions.
  #
  # arecord -l # list available audio devices
  #
  # Note: some voice-identification or microphone-based tools expect ALSA's
  # default device to be configured in the user's `~/.asoundrc`. If your mic
  # is on ALSA card 0, for example, create `~/.asoundrc` with:
  #
  # You can manage this file via Home Manager in your `users/<you>/home.nix`:
  #
  # home.file.".asoundrc".text = ''
  # defaults.pcm.card 0
  # defaults.ctl.card 0
  # '';
  home.file.".asoundrc".text = ''
    defaults.pcm.card 0
    defaults.ctl.card 0
  '';
}
