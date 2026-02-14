# Audio policy:
# - PipeWire is the audio server on all platforms.
# - Nix apps must use PulseAudio protocol (ao=pulse), never ao=pipewire.
#   Nix's libpipewire version mismatches Ubuntu's system pipewire (ABI break = silence).
#   PulseAudio protocol is version-independent — pipewire-pulse bridges it.
# - bluetooth-policy.nix is the single source of truth for BT values,
#   consumed by both Ubuntu (WirePlumber 0.4 Lua) and NixOS (WirePlumber 0.5 conf).
# - WirePlumber config format is platform-specific and cannot be unified:
#   Ubuntu uses Lua via xdg.configFile, NixOS uses declarative conf via wireplumber.extraConfig.
# - The BT autoswitch service is cross-platform (pactl speaks PulseAudio protocol).
{
  lib,
  isNixOS,
  pkgs,
  ...
}:
let
  btPolicy = import ./bluetooth-policy.nix;
in
{
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

  xdg.configFile = lib.mkIf (!isNixOS) {
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
          ["priority.driver"] = ${toString btPolicy.inputPriority},
          ["priority.session"] = ${toString btPolicy.inputPriority},
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
          ["bluez5.auto-connect"] = { ${
            lib.concatMapStringsSep ", " (c: ''"${c}"'') btPolicy.autoConnect
          } },
          ["bluez5.codecs"] = { ${lib.concatMapStringsSep ", " (c: ''"${c}"'') btPolicy.codecs} },
          ["bluez5.autoswitch-to-headset-profile"] = ${lib.boolToString btPolicy.autoswitchToHeadsetProfile},
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
          ["priority.driver"] = ${toString btPolicy.sinkPriority},
          ["priority.session"] = ${toString btPolicy.sinkPriority},
        },
      })
    '';
  };
}
