{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../tests/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

  hasService = name: builtins.hasAttr name cfg.systemd.user.services;

  wireplumberLocaleDropinPath = "systemd/user/wireplumber.service.d/force-c-locale-for-ascii-safe-device-descriptions.conf";
  wireplumberLocaleDropinExists = builtins.hasAttr wireplumberLocaleDropinPath cfg.xdg.configFile;
  wireplumberLocaleDropinContainsLangC =
    wireplumberLocaleDropinExists
    && builtins.match ".*LANG=C.*" cfg.xdg.configFile.${wireplumberLocaleDropinPath}.text != null;

  echoCancelDropinPath = "pipewire/pipewire.conf.d/20-echo-cancel.conf";
  echoCancelDropinExists = builtins.hasAttr echoCancelDropinPath cfg.xdg.configFile;
  echoCancelDropinConfig =
    if echoCancelDropinExists then
      builtins.fromJSON cfg.xdg.configFile.${echoCancelDropinPath}.text
    else
      { };
  echoCancelModule =
    if echoCancelDropinExists then
      lib.findFirst (
        m: m.name == "libpipewire-module-echo-cancel"
      ) null echoCancelDropinConfig."context.modules"
    else
      null;
  echoCancelSourceDescriptionMatchesVoicePipelineLookup =
    echoCancelModule != null
    && echoCancelModule.args."source.props"."node.description" == "echo-cancel-source";
in
{
  domain-audio-bluetooth-service =
    mkEvalCheck "domain-audio-bluetooth-service" (hasService "bluetooth-audio-autoswitch")
      "bluetooth audio autoswitch service should exist";

  domain-audio-wireplumber-locale-dropin =
    mkEvalCheck "domain-audio-wireplumber-locale-dropin" wireplumberLocaleDropinContainsLangC
      "WirePlumber systemd drop-in must set LANG=C to prevent non-ASCII device descriptions that break pactl JSON output";

  domain-audio-echo-cancel-source-description-matches-voice-pipeline =
    mkEvalCheck "domain-audio-echo-cancel-source-description-matches-voice-pipeline"
      echoCancelSourceDescriptionMatchesVoicePipelineLookup
      "Echo-cancel source node.description must equal 'echo-cancel-source' because voice-pipeline's audio_env.discover() parses wpctl status output (which shows node.description, not node.name) and substring-matches VOICE_PIPELINE_CAPTURE_DEVICE='echo-cancel-source'";
}
