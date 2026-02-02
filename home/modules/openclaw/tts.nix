{ lib, config, ... }:
let
  inherit (config) openclaw;
  inherit (openclaw) tts;
in
{
  options.openclaw.tts = {
    voice = lib.mkOption {
      type = lib.types.str;
      default = "en-US-GuyNeural";
      description = "Default edge-tts voice for this agent";
    };

    engine = lib.mkOption {
      type = lib.types.str;
      default = "edge-tts";
      description = "TTS engine to use";
    };
  };

  config.home.file = openclaw.deployToWorkspace {
    "tts.json".text = builtins.toJSON {
      inherit (tts) engine;
      inherit (tts) voice;
    };
  };
}
