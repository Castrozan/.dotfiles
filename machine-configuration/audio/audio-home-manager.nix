{
  lib,
  isNixOS,
  pkgs,
  ...
}:
let
  btPolicy = import ./bluetooth-policy.nix;

  moveAllStreamsToDefaultSink = pkgs.writeShellScriptBin "move-all-streams-to-default-sink" (
    builtins.readFile ./scripts/move-all-streams-to-default-sink
  );

  bluetoothAudioAutoswitch = pkgs.writeShellScriptBin "bluetooth-audio-autoswitch" (
    builtins.readFile ./scripts/bluetooth-audio-autoswitch
  );

  bluetoothAudioAutoswitchToolPath = lib.makeBinPath [
    pkgs.pulseaudio
    pkgs.gawk
    pkgs.gnugrep
    pkgs.coreutils
    moveAllStreamsToDefaultSink
  ];
in
{
  imports = [ ./audio-scripts-home-manager.nix ];
  systemd.user.services.unmute-alsa-headphone-on-pipewire-start = {
    Unit = {
      Description = "Unmute ALSA headphone switch after PipeWire starts (UCM init.conf mutes it)";
      After = [ "wireplumber.service" ];
      Requires = [ "wireplumber.service" ];
    };
    Service = {
      Type = "oneshot";
      ExecStartPre = "${pkgs.coreutils}/bin/sleep 2";
      ExecStart =
        let
          script = pkgs.writeShellScript "unmute-alsa-headphone" ''
            ${pkgs.alsa-utils}/bin/amixer -c 0 sset Headphone unmute >/dev/null 2>&1 || true
            ${pkgs.alsa-utils}/bin/amixer -c 0 sset Headphone 100% >/dev/null 2>&1 || true
          '';
        in
        "${script}";
    };
    Install = {
      WantedBy = [ "wireplumber.service" ];
    };
  };

  systemd.user.services.bluetooth-audio-autoswitch = {
    Unit = {
      Description = "Auto-switch audio sink on Bluetooth connect/disconnect";
      After = [ "pipewire-pulse.service" ];
    };
    Service = {
      Environment = "PATH=${bluetoothAudioAutoswitchToolPath}";
      ExecStart = "${bluetoothAudioAutoswitch}/bin/bluetooth-audio-autoswitch";
      Restart = "always";
      RestartSec = 5;
    };
    Install = {
      WantedBy = [ "pipewire-pulse.service" ];
    };
  };

  xdg.configFile = lib.mkIf (!isNixOS) {
    "pipewire/pipewire.conf.d/05-realtime-scheduling.conf".text = builtins.toJSON {
      "context.modules" = [
        {
          name = "libpipewire-module-rt";
          args = {
            "nice.level" = -11;
            "rt.prio" = 88;
            "rt.time.soft" = 2000000;
            "rt.time.hard" = 2000000;
          };
          flags = [
            "ifexists"
            "nofail"
          ];
        }
      ];
    };

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
          ["priority.driver"] = ${toString btPolicy.laptopMicPriority},
          ["priority.session"] = ${toString btPolicy.laptopMicPriority},
        },
      })
    '';

    "wireplumber/main.lua.d/41-disable-stream-restore-target.lua".text = ''
      stream_defaults.properties["restore-target"] = ${lib.boolToString btPolicy.restoreStreamTarget}
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

    "systemd/user/wireplumber.service.d/force-c-locale-for-ascii-safe-device-descriptions.conf".text =
      ''
        [Service]
        Environment=LANG=C
      '';
  };
}
