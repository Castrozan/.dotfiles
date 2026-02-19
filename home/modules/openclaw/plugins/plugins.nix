{ lib, ... }:
{
  config = {
    openclaw.configDeletes = [
      ".memory"
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

      ".plugins.entries.hindsight-openclaw" = {
        enabled = false;
      };

      ".plugins.entries.memory-core" = {
        enabled = false;
      };

      ".plugins.installs" = { };
    };
  };
}
