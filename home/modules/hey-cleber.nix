# Hey Cleber — Always-on voice assistant for Clawdbot
# https://github.com/castrozan/hey-cleber
{ inputs, pkgs, ... }:
{
  imports = [ inputs.hey-cleber.homeManagerModules.hey-cleber ];

  services.hey-cleber = {
    enable = true;
    keywords = [
      "cleber"
      "kleber"
      "clever"
      "cleaver"
      "clebert"
      "kleiber"
      "klebber"
      "cleyber"
      "klever"
    ];
    gatewayUrl = "http://localhost:18789";
    whisperBin = "${pkgs.openai-whisper}/bin/whisper";
    mpvBin = "${pkgs.mpv}/bin/mpv";
  };
}
