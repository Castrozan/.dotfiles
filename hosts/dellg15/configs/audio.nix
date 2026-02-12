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

      "30-echo-cancel" = {
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
    };

    wireplumber.extraConfig = {
      "50-disable-acp-card" = {
        "monitor.alsa.rules" = [
          {
            matches = [
              { "device.name" = "~alsa_card.pci-0000_05_00.5.*"; }
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
              "priority.driver" = btPolicy.inputPriority;
              "priority.session" = btPolicy.inputPriority;
            };
          }
          {
            matches = [
              { "node.name" = "alsa_input.pci-0000_05_00.6.HiFi__Mic1__source"; }
            ];
            actions.update-props = {
              "priority.driver" = 2500;
              "priority.session" = 2500;
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
