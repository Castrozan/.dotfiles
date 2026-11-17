{
  config,
  lib,
  isNixOS,
  ...
}:
let
  bridgeSettings = config.clawdeDiscordVoiceBridge;
  silverCharacter = "darkness-shibu";
in
{
  config =
    lib.mkIf (isNixOS && bridgeSettings != null && bridgeSettings.conversationProfile != null)
      {
        systemd.user.services.silver-voice-holder = {
          Unit = {
            Description = "Silver holding the avatar floor in the silver voice channel";
            X-SwitchMethod = "keep-old";
          };
          Service = {
            ExecStart = "${config.home.profileDirectory}/bin/avatar-voice-holder --hermes-profile ${bridgeSettings.conversationProfile} --character ${silverCharacter}";
            Environment = [ "PATH=${config.home.profileDirectory}/bin:/run/current-system/sw/bin" ];
            WorkingDirectory = config.home.homeDirectory;
            TimeoutStopSec = "150s";
          };
        };
      };
}
