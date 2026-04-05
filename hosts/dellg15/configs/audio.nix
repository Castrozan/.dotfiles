{ config, pkgs, ... }:
let
  btPolicy = import ../../../home/modules/audio/bluetooth-policy.nix;
in
{
  assertions = [
    {
      assertion = config.services.pipewire.enable;
      message = "PipeWire is required — the audio pipeline depends on PipeWire for low-latency mixing, Bluetooth codec negotiation, and JACK compatibility; PulseAudio alone cannot provide these";
    }
    {
      assertion = !config.services.pulseaudio.enable;
      message = "PulseAudio must be disabled — PipeWire provides its own PulseAudio compatibility layer; running both causes socket conflicts and silent audio routing failures";
    }
    {
      assertion = config.security.rtkit.enable;
      message = "rtkit is required — PipeWire needs real-time scheduling priority to prevent audio dropouts under CPU load; without rtkit the audio thread runs at normal priority and glitches during builds";
    }
    {
      assertion = config.hardware.bluetooth.enable;
      message = "Bluetooth must be enabled — the audio pipeline relies on Bluetooth for wireless headset connectivity and WirePlumber codec negotiation (SBC-XQ, AAC, aptX)";
    }
  ];

  security.rtkit.enable = true;

  hardware.bluetooth = {
    enable = true;
    powerOnBoot = true;
    settings.General = {
      Enable = "Source,Sink,Media,Socket";
      Experimental = true;
    };
  };

  services.pulseaudio.enable = false;

  services.pipewire = {
    enable = true;
    alsa = {
      enable = true;
      support32Bit = true;
    };
    pulse.enable = true;
    jack.enable = true;

    extraConfig.pipewire = {
      "10-clock-rate" = {
        "context.properties" = {
          "default.clock.rate" = 48000;
          "default.clock.allowed-rates" = [
            44100
            48000
          ];
        };
      };

    };

    wireplumber.extraConfig = {
      "40-stream-defaults" = {
        "stream.rules" = [
          {
            matches = [
              { "node.name" = "~*"; }
            ];
            actions.update-props = {
              "stream.restore-target" = btPolicy.restoreStreamTarget;
            };
          }
        ];
      };

      "50-disable-unused-audio-cards" = {
        "monitor.alsa.rules" = [
          {
            matches = [
              { "device.name" = "~alsa_card.pci-0000_05_00.5.*"; }
            ];
            actions.update-props = {
              "device.disabled" = true;
            };
          }
          {
            matches = [
              { "device.name" = "alsa_card.pci-0000_01_00.1"; }
            ];
            actions.update-props = {
              "device.disabled" = true;
            };
          }
          {
            matches = [
              { "device.name" = "alsa_card.pci-0000_05_00.1"; }
            ];
            actions.update-props = {
              "device.disabled" = true;
            };
          }
        ];
      };

      "50-realtek-source-priority" = {
        "monitor.alsa.rules" = [
          {
            matches = [
              { "node.name" = "~alsa_input.pci-0000_05_00.6.*"; }
            ];
            actions.update-props = {
              "priority.driver" = btPolicy.laptopMicPriority;
              "priority.session" = btPolicy.laptopMicPriority;
            };
          }
          {
            matches = [
              { "node.name" = "alsa_input.pci-0000_05_00.6.HiFi__Mic1__source"; }
            ];
            actions.update-props = {
              "priority.driver" = btPolicy.laptopMicPriority + 100;
              "priority.session" = btPolicy.laptopMicPriority + 100;
            };
          }
        ];
      };

      "50-bluetooth-codec-preference" = {
        "monitor.bluez.rules" = [
          {
            matches = [
              { "device.name" = "~bluez_card.*"; }
            ];
            actions.update-props = {
              "bluez5.auto-connect" = btPolicy.autoConnect;
              "bluez5.codecs" = btPolicy.codecs;
              "bluez5.autoswitch-to-headset-profile" = btPolicy.autoswitchToHeadsetProfile;
            };
          }
        ];
      };

      "51-bluetooth-sink-priority" = {
        "monitor.bluez.rules" = [
          {
            matches = [
              { "node.name" = "~bluez_output.*"; }
            ];
            actions.update-props = {
              "priority.driver" = btPolicy.sinkPriority;
              "priority.session" = btPolicy.sinkPriority;
            };
          }
        ];
      };
    };
  };

  environment.systemPackages = with pkgs; [
    alsa-utils
    pulseaudio
  ];
}
