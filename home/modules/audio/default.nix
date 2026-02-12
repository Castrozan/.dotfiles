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

    "wireplumber/main.lua.d/90-bluetooth-autoswitch-default.lua".text = ''
      local nodes_om = ObjectManager {
        Interest {
          type = "node",
          Constraint { "media.class", "=", "Audio/Sink" },
        }
      }

      local default_metadata_om = ObjectManager {
        Interest {
          type = "metadata",
          Constraint { "metadata.name", "=", "default" },
        }
      }

      nodes_om:connect("object-added", function(_, node)
        local name = node.properties["node.name"]
        if not name or not string.find(name, "^bluez_output%.") then
          return
        end

        local metadata = default_metadata_om:lookup()
        if metadata then
          metadata:set(0, "default.configured.audio.sink", "Spa:String:JSON",
            '{ "name": "' .. name .. '" }')
        end
      end)

      nodes_om:activate()
      default_metadata_om:activate()
    '';
  };
}
