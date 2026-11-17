{
  pkgs,
  lib,
  programs,
}:
lib.makeBinPath [
  programs.audio
  (import ../../media-generation/speech-package.nix { inherit pkgs; })
  pkgs.ffmpeg
  pkgs.piper-tts
  pkgs.pulseaudio
]
