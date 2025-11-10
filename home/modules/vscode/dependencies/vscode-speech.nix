{ pkgs, ... }:
{
  # Ensure ALSA libraries are available for any speech/voice extensions.
  #
  # Note: some voice-identification or microphone-based tools expect ALSA's
  # default device to be configured in the user's `~/.asoundrc`. If your mic
  # is on ALSA card 2, for example, create `~/.asoundrc` with:
  #
  # defaults.pcm.card 2
  # defaults.ctl.card 2
  #
  # You can manage this file via Home Manager in your `users/<you>/home.nix`:
  #
  # home.file.".asoundrc".text = ''
  # defaults.pcm.card 2
  # defaults.ctl.card 2
  # '';

  home.packages = with pkgs; [
    alsa-lib
  ];
}
