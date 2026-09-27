{ config, ... }:
{
  imports = [ ../configuration/audiobooks/audiobook-provisioner-nixos.nix ];

  custom.audiobookProvisioner = {
    enable = true;
    audiobookshelfBaseUrl = "http://arr:13378";
    readmeabookBaseUrl = "http://arr:3030";
    prowlarrBaseUrl = "http://arr:9696";
    prowlarrConfigFile = "/home/zanoni/arr-stack/config/prowlarr/config.xml";
    passwordFile = config.age.secrets."arr-qbittorrent-password".path;
    username = "lucas";
  };

  systemd.services.arr-audiobook-provisioner.restartTriggers = [
    ../../../../secrets/credentials/media/arr-qbittorrent-password.age
  ];
}
