# Hey Clever — Always-on voice assistant for Clawdbot
# https://github.com/castrozan/hey-cleber
{ inputs, pkgs, ... }:
{
  imports = [ inputs.hey-cleber.homeManagerModules.hey-clever ];

  services.hey-clever = {
    enable = true;
    keywords = [
      "clever"
      "klever"
      "cleber"
      "kleber"
      "cleaver"
      "clevert"
      "kleiber"
      "klebber"
      "cleyber"
    ];
    gatewayUrl = "http://localhost:18789";
    whisperBin = "${pkgs.openai-whisper}/bin/whisper";
    mpvBin = "${pkgs.mpv}/bin/mpv";
  };

  # Load gateway token from agenix-decrypted secret (not hardcoded)
  systemd.user.services.hey-clever.Service.EnvironmentFile = "/run/agenix/openclaw-gateway-token";
}
