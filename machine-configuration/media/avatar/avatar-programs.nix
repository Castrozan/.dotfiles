{ pkgs, lib }:
let
  control = import ./control-package.nix { inherit pkgs; };
  renderer = import ./renderer-package.nix { inherit pkgs; };
  speakerModel = pkgs.fetchurl {
    url = "https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/3dspeaker_speech_campplus_sv_zh_en_16k-common_advanced.onnx";
    sha256 = "18pb1kqg82x3qa07yd4b6n6yjmvbdmfh7xckjdm5h41sjqbgqg5a";
  };
  turnModel = pkgs.fetchurl {
    url = "https://huggingface.co/pipecat-ai/smart-turn-v3/resolve/f766f81d3cfdf7737ac64aad813d91bbfd56bf93/smart-turn-v3.2-cpu.onnx";
    sha256 = "2bb026316b14a660486a75b1733cd3fbab8c2fd0314dc9af7be49f8cca967e4f";
  };
  listenerPython = pkgs.python3.withPackages (
    packages: with packages; [
      numpy
      onnxruntime
      sherpa-onnx
    ]
  );
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
    export AVATAR_SPEAKER_MODEL=${speakerModel}
    export AVATAR_TURN_MODEL=${turnModel}
    export PYTHONPATH=${./scripts/listening}
    exec ${listenerPython}/bin/python3 ${./scripts/listening/listener.py}
  '';
  talk = pkgs.writeShellScriptBin "avatar-talk" ''
    export PATH=${
      lib.makeBinPath [
        audio
        command
        stop
        pkgs.hyprland
        pkgs.pulseaudio
        pkgs.systemd
      ]
    }:$PATH
    export PYTHONPATH=${./scripts}:${./scripts/listening}:${./scripts/conversation}
    exec ${pkgs.python312}/bin/python3 ${./scripts/conversation/talk_cli.py} "$@"
  '';
in
{
  inherit
    audio
    browserRuntime
    camera
    command
    control
    controls
    listen
    listener
    serve
    start
    stop
    talk
    ;
}
