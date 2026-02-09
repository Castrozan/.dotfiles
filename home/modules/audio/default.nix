{ lib, isNixOS, ... }:
lib.mkIf (!isNixOS) {
  xdg.configFile = {
    "pipewire/pipewire.conf.d/10-clock-rate.conf".text = builtins.toJSON {
      "context.properties" = {
        "default.clock.rate" = 48000;
        "default.clock.allowed-rates" = [
          44100
          48000
        ];
      };
    };

    "pipewire/pipewire.conf.d/30-echo-cancel.conf".text = builtins.toJSON {
      "context.modules" = [
        {
          name = "libpipewire-module-echo-cancel";
          args = {
            "library.name" = "aec/libspa-aec-webrtc";
            "node.name" = "Echo Cancel Source";
            "node.description" = "Echo Cancel Source";
            "audio.rate" = 48000;
            "audio.channels" = 1;
            "source.props" = {
              "node.name" = "echo-cancel-source";
              "media.class" = "Audio/Source";
              "audio.position" = [ "MONO" ];
            };
            "sink.props" = {
              "node.name" = "echo-cancel-sink";
              "media.class" = "Audio/Sink";
              "audio.position" = [ "MONO" ];
            };
          };
        }
      ];
    };

    "wireplumber/main.lua.d/50-disable-bt-autoswitch.lua".text = ''
      table.insert(alsa_monitor.rules, {
        matches = {
          {
            { "node.name", "matches", "alsa_input.*" },
          },
        },
        apply_properties = {
          ["priority.driver"] = 2000,
          ["priority.session"] = 2000,
        },
      })
    '';

    "wireplumber/bluetooth.lua.d/50-bluetooth-codec-preference.lua".text = ''
      table.insert(bluez_monitor.rules, {
        matches = {
          {
            { "device.name", "matches", "bluez_card.*" },
          },
        },
        apply_properties = {
          ["bluez5.auto-connect"] = { "a2dp_sink", "a2dp_source" },
          ["bluez5.codecs"] = { "aac", "sbc_xq", "sbc" },
          ["bluez5.autoswitch-to-headset-profile"] = false,
        },
      })
    '';

    "wireplumber/bluetooth.lua.d/51-bluetooth-sink-priority.lua".text = ''
      table.insert(bluez_monitor.rules, {
        matches = {
          {
            { "node.name", "matches", "bluez_output.*" },
          },
        },
        apply_properties = {
          ["priority.driver"] = 3000,
          ["priority.session"] = 3000,
        },
      })
    '';
  };
}
