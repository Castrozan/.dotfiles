{
  pkgs,
  lib,
  isNixOS,
  ...
}:
let
  control = import ./control-package.nix { inherit pkgs; };
  renderer = import ./renderer-package.nix { inherit pkgs; };
  audio = pkgs.writeShellScriptBin "avatar-audio" ''
    export PATH=${lib.makeBinPath [ pkgs.pulseaudio ]}:$PATH
    export PYTHONPATH=${./scripts}
    exec ${pkgs.python312}/bin/python3 ${./scripts/audio_cli.py} "$@"
  '';
  serve = pkgs.writeShellScript "avatar-renderer" ''
    export AVATAR_RENDERER_ROOT=${renderer}
    exec ${pkgs.python312}/bin/python3 ${./scripts/serve.py}
  '';
  browserRuntime = ../../../agent-harness/agent-instructions/skills/workstation/avatar/scripts/browser/runtime.py;
  camera = pkgs.writeShellScript "avatar-camera" ''
    export CDP_PORT="$(${pkgs.python312}/bin/python3 ${browserRuntime} endpoint)"
    export PATH=${
      lib.makeBinPath [
        pkgs.ffmpeg
        pkgs.chromium
      ]
    }:$PATH
    exec ${pkgs.nodejs_22}/bin/node ${control}/virtual-camera.js --fps 60 --width 1280 --height 720
  '';
  controls = pkgs.writeShellScriptBin "avatar-controls" ''
    export PATH=${lib.makeBinPath [ pkgs.chromium ]}:$PATH
    exec ${pkgs.python312}/bin/python3 ${browserRuntime} controls
  '';
  command = pkgs.writeShellScriptBin "avatar-command" ''
    export NODE_PATH=${control}/node_modules
    exec ${pkgs.nodejs_22}/bin/node ${./scripts/command.js} "$@"
  '';
  start = pkgs.writeShellScriptBin "avatar-start" ''
    export PATH=${
      lib.makeBinPath [
        audio
        pkgs.systemd
        pkgs.v4l-utils
      ]
    }:$PATH
    exec ${pkgs.python312}/bin/python3 ${./scripts/start.py}
  '';
  stop = pkgs.writeShellScriptBin "avatar-stop" ''
    export PATH=${
      lib.makeBinPath [
        audio
        pkgs.systemd
      ]
    }:$PATH
    ${builtins.readFile ./scripts/avatar-stop}
  '';
  windowPresence =
    action: "${pkgs.python312}/bin/python3 ${./scripts/conversation/desktop_window.py} ${action}";
  listen = pkgs.writeShellScriptBin "avatar-listen" ''
    export PATH=${
      lib.makeBinPath [
        pkgs.pulseaudio
        pkgs.systemd
      ]
    }:$PATH
    export PYTHONPATH=${./scripts/listening}
    exec ${pkgs.python312}/bin/python3 ${./scripts/listening/listen_cli.py} "$@"
  '';
  listener = pkgs.writeShellScript "avatar-listener" ''
    export PATH=${
      lib.makeBinPath [
        command
        pkgs.pulseaudio
      ]
    }:$PATH
    export PYTHONPATH=${./scripts/listening}
    exec ${pkgs.python312}/bin/python3 ${./scripts/listening/listener.py}
  '';
  talk = pkgs.writeShellScriptBin "avatar-talk" ''
    export PATH=${
      lib.makeBinPath [
        audio
        command
        stop
        pkgs.pulseaudio
        pkgs.systemd
      ]
    }:$PATH
    export PYTHONPATH=${./scripts}:${./scripts/listening}:${./scripts/conversation}
    exec ${pkgs.python312}/bin/python3 ${./scripts/conversation/talk_cli.py} "$@"
  '';
  transcriptionModel = pkgs.fetchurl {
    url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small-q5_1.bin";
    sha256 = "1fqi0h90ig4ifpyb44cfc7dmnndv2vy5mr9g22yng9fp6nly91df";
  };
  speechVoices = import ./speech-voices.nix { inherit pkgs; };
  tools = lib.makeBinPath [
    audio
    (import ../media-generation/speech-package.nix { inherit pkgs; })
    pkgs.ffmpeg
    pkgs.piper-tts
    pkgs.pulseaudio
  ];
  serviceUnit = {
    PartOf = [ "avatar.target" ];
    After = [ "avatar-audio.service" ];
    Requires = [ "avatar-audio.service" ];
  };
in
{
  config = lib.mkIf isNixOS {
    home.packages = [
      audio
      command
      controls
      listen
      start
      stop
      talk
    ];
    systemd.user = {
      targets.avatar.Unit = {
        Description = "Local avatar media";
        Requires = [
          "avatar-audio.service"
          "avatar-control-server.service"
          "avatar-renderer.service"
          "avatar-browser.service"
          "avatar-camera.service"
        ];
      };
      targets.avatar-conversation.Unit = {
        Description = "Avatar desktop conversation";
        Requires = [
          "avatar-audio.service"
          "avatar-control-server.service"
          "avatar-renderer.service"
          "avatar-room-microphone.service"
          "avatar-window.service"
        ];
        BindsTo = [ "avatar-browser.service" ];
        After = [ "avatar-browser.service" ];
      };
      services = {
        avatar-audio = {
          Unit = {
            Description = "Isolated avatar audio mix";
            PartOf = [ "avatar.target" ];
          };
          Service = {
            Type = "oneshot";
            RemainAfterExit = true;
            ExecStart = "${audio}/bin/avatar-audio start";
            ExecStop = "${audio}/bin/avatar-audio stop";
          };
        };
        avatar-control-server = {
          Unit = serviceUnit // {
            Description = "Avatar control server";
          };
          Service = {
            ExecStart = "${pkgs.nodejs_22}/bin/node ${control}/server.js";
            Environment = [
              "PATH=${tools}"
              "AVATAR_CLOUD_VOICE=cgSgspJ2msm6clMCkdW9"
              "AVATAR_TTS_VOICE=pt_BR-faber-medium"
              "AVATAR_TTS_VOICE_DIRECTORY=${speechVoices}"
              "AVATAR_AUDIO_MONITOR=AvatarLipSync.monitor"
              "XDG_RUNTIME_DIR=/run/user/%U"
            ];
            Restart = "on-failure";
          };
          Install.WantedBy = [ "avatar.target" ];
        };
        avatar-browser = {
          Unit = {
            Description = "Avatar output browser";
            PartOf = [ "avatar.target" ];
            After = [
              "avatar-renderer.service"
              "avatar-control-server.service"
            ];
            Requires = [
              "avatar-renderer.service"
              "avatar-control-server.service"
            ];
          };
          Service = {
            ExecStart = "${pkgs.python312}/bin/python3 ${browserRuntime} supervise http://localhost:3000/?output=1";
            ExecStopPost = "${pkgs.python312}/bin/python3 ${browserRuntime} stop";
            Environment = [ "PATH=${lib.makeBinPath [ pkgs.chromium ]}" ];
            KillMode = "mixed";
          };
          Install.WantedBy = [ "avatar.target" ];
        };
        avatar-camera = {
          Unit = {
            Description = "Avatar virtual camera";
            PartOf = [ "avatar.target" ];
            After = [ "avatar-browser.service" ];
            Requires = [ "avatar-browser.service" ];
          };
          Service = {
            ExecStart = toString camera;
            Environment = [ "V4L2_DEVICE=/dev/video10" ];
            Restart = "on-failure";
          };
          Install.WantedBy = [ "avatar.target" ];
        };
        avatar-room-microphone = {
          Unit = {
            Description = "Avatar microphone with desktop audio cancelled";
            PartOf = [ "avatar-conversation.target" ];
          };
          Service = {
            ExecStart = "${pkgs.pipewire}/bin/pipewire -c ${./room-microphone.conf}";
            Restart = "on-failure";
          };
        };
        avatar-window = {
          Unit = {
            Description = "Avatar window on the desktop";
            PartOf = [
              "avatar-conversation.target"
              "avatar-browser.service"
            ];
            After = [ "avatar-browser.service" ];
            Requires = [ "avatar-browser.service" ];
          };
          Service = {
            Type = "oneshot";
            RemainAfterExit = true;
            ExecStart = windowPresence "show";
            ExecStop = windowPresence "hide";
            Environment = [ "PATH=${lib.makeBinPath [ pkgs.hyprland ]}" ];
          };
        };
        avatar-transcriber = {
          Unit = {
            Description = "Local avatar speech transcription";
            StopWhenUnneeded = true;
          };
          Service = {
            ExecStart = "${pkgs.whisper-cpp-vulkan}/bin/whisper-server --host 127.0.0.1 --port 8767 --model ${transcriptionModel} --language auto --threads 4";
            Restart = "on-failure";
          };
        };
        avatar-listener = {
          Unit = {
            Description = "Local avatar meeting listener";
            PartOf = [ "avatar-conversation.target" ];
            After = [ "avatar-transcriber.service" ];
            Requires = [ "avatar-transcriber.service" ];
          };
          Service = {
            ExecStart = toString listener;
            Restart = "on-failure";
          };
        };
        avatar-renderer = {
          Unit = serviceUnit // {
            Description = "Offline avatar renderer";
          };
          Service = {
            ExecStart = toString serve;
            Restart = "on-failure";
          };
          Install.WantedBy = [ "avatar.target" ];
        };
      };
    };
  };
}
