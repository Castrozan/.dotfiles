{
  helpers,
  pkgs,
  lib,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../audio-home-manager.nix ];

  hasService = name: builtins.hasAttr name cfg.systemd.user.services;

  nixosAudio = self.nixosConfigurations.chise.config;
  recoveryService = nixosAudio.systemd.user.services.pipewire-alsa-recovery;

  wireplumberLocaleDropinPath = "systemd/user/wireplumber.service.d/force-c-locale-for-ascii-safe-device-descriptions.conf";
  wireplumberLocaleDropinExists = builtins.hasAttr wireplumberLocaleDropinPath cfg.xdg.configFile;
  wireplumberLocaleDropinContainsLangC =
    wireplumberLocaleDropinExists
    && builtins.match ".*LANG=C.*" cfg.xdg.configFile.${wireplumberLocaleDropinPath}.text != null;
in
{
  domain-audio-alsa-failure-recovery =
    mkEvalCheck "domain-audio-alsa-failure-recovery"
      (
        builtins.elem "default.target" recoveryService.wantedBy
        && builtins.elem "pipewire.service" recoveryService.after
        && recoveryService.partOf == [ ]
        && recoveryService.serviceConfig.Restart == "on-failure"
        && recoveryService.serviceConfig.MemoryMax == "64M"
        && recoveryService.unitConfig.ConditionGroup == "!gdm"
      )
      "the ALSA failure monitor must start with the user session, skip the login screen greeter whose journal it cannot read, and survive audio restarts with bounded resources";

  domain-audio-streams-follow-default =
    mkEvalCheck "domain-audio-streams-follow-default"
      (
        !nixosAudio.services.pipewire.wireplumber.extraConfig."40-stream-defaults"."wireplumber.settings"."node.stream.restore-target"
      )
      "WirePlumber must use its native setting to prevent stale stream targets after headset disconnects";

  domain-audio-bluetooth-service =
    mkEvalCheck "domain-audio-bluetooth-service" (hasService "bluetooth-audio-autoswitch")
      "bluetooth audio autoswitch service should exist";

  domain-audio-wireplumber-locale-dropin =
    mkEvalCheck "domain-audio-wireplumber-locale-dropin" wireplumberLocaleDropinContainsLangC
      "WirePlumber systemd drop-in must set LANG=C to prevent non-ASCII device descriptions that break pactl JSON output";
}
