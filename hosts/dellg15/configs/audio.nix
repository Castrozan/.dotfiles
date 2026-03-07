{ pkgs, ... }:
let
  btPolicy = import ../../../home/modules/audio/bluetooth-policy.nix;
in
{
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
