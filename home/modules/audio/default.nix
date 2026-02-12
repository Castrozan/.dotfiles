{
  lib,
  isNixOS,
  pkgs,
  ...
}:
lib.mkIf (!isNixOS) {
  systemd.user.services.bluetooth-audio-autoswitch = {
    Unit = {
      Description = "Auto-switch default audio sink to Bluetooth on connect";
      After = [ "pipewire-pulse.service" ];
    };
    Service = {
      ExecStart =
        let
          script = pkgs.writeShellScript "bluetooth-audio-autoswitch" ''
            ${pkgs.pulseaudio}/bin/pactl subscribe | while read -r line; do
              if echo "$line" | ${pkgs.gnugrep}/bin/grep -q "'new' on sink"; then
                sink_index=$(echo "$line" | ${pkgs.gnugrep}/bin/grep -oP '#\K\d+')
                sink_name=$(${pkgs.pulseaudio}/bin/pactl list sinks short | ${pkgs.gawk}/bin/awk -v idx="$sink_index" '$1 == idx { print $2 }')
                if [[ "$sink_name" == bluez_output.* ]]; then
                  ${pkgs.pulseaudio}/bin/pactl set-default-sink "$sink_name"
                fi
              fi
            done
          '';
        in
        "${script}";
      Restart = "always";
      RestartSec = 5;
    };
    Install = {
      WantedBy = [ "pipewire-pulse.service" ];
    };
  };

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

  };
}
