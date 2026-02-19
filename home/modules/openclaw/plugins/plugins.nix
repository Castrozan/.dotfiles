{ lib, ... }:
{
  config = {
    openclaw.configDeletes = [
      ".memory"
      ".plugins.entries.hindsight-openclaw"
      ".plugins.entries.memory-core"
      ".plugins.slots.memory"
    ];

    openclaw.configPatches = lib.mkOptionDefault {
      ".plugins.allow" = [
        "telegram"
        "device-pair"
        "phone-control"
        "talk-voice"
        "discord"
      ];

      ".plugins.installs" = { };
    };
  };
}
