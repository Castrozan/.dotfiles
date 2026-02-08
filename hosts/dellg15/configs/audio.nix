{ pkgs, ... }:
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

    extraConfig.pipewire."30-echo-cancel" = {
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
              "priority.driver" = 2000;
              "priority.session" = 2000;
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
              "bluez5.auto-connect" = [
                "a2dp_sink"
                "a2dp_source"
              ];
              "bluez5.codecs" = [
                "aac"
                "sbc_xq"
                "sbc"
              ];
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
