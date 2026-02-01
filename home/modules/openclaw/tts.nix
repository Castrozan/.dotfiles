{ lib, config, ... }:
let
  cfg = config.openclaw.tts;
in
{
  options.openclaw.tts = {
    voice = lib.mkOption {
      type = lib.types.str;
      default = "en-US-GuyNeural";
      description = "Default edge-tts voice for this agent";
    };

    voiceAlt = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Alternative voice for secondary language";
    };

    engine = lib.mkOption {
      type = lib.types.str;
      default = "edge-tts";
      description = "TTS engine to use";
    };
  };

  config.home.file."clawd/.nix/tts.json" = {
    text = builtins.toJSON {
      engine = cfg.engine;
      voice = cfg.voice;
      voiceAlt = cfg.voiceAlt;
    };
  };
}
