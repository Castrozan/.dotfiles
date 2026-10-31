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
    export CDP_PORT="$(${pkgs.python312}/bin/python3 ${browserRuntime} start 'http://localhost:3000/?output=1')"
    export PATH=${
      lib.makeBinPath [
        pkgs.ffmpeg
        pkgs.chromium
      ]
    }:$PATH
    exec ${pkgs.nodejs_22}/bin/node ${control}/virtual-camera.js --fps 15 --width 1280 --height 720
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
        pkgs.systemd
        pkgs.v4l-utils
      ]
    }:$PATH
    exec ${pkgs.python312}/bin/python3 ${./scripts/start.py}
  '';
  stop = pkgs.writeShellScriptBin "avatar-stop" ''
    systemctl --user stop avatar.target
    if systemctl --user is-failed --quiet avatar-audio.service; then
      echo "Avatar audio cleanup is incomplete; inspect avatar-audio status, then retry avatar-audio stop" >&2
      exit 1
    fi
  '';
  tools = lib.makeBinPath [
    pkgs.ffmpeg
    pkgs.pulseaudio
    pkgs.python3Packages.edge-tts
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
      start
      stop
    ];
    systemd.user.targets.avatar.Unit = {
      Description = "Local avatar media";
      Requires = [
        "avatar-audio.service"
        "avatar-control-server.service"
        "avatar-renderer.service"
        "avatar-camera.service"
      ];
    };
    systemd.user.services.avatar-audio = {
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
    systemd.user.services.avatar-control-server = {
      Unit = serviceUnit // {
        Description = "Avatar control server";
      };
      Service = {
        ExecStart = "${pkgs.nodejs_22}/bin/node ${control}/server.js";
        Environment = [
          "PATH=${tools}"
          "AVATAR_TTS_VOICE=pt-BR-AntonioNeural"
          "AVATAR_AUDIO_MONITOR=AvatarMic.monitor"
          "XDG_RUNTIME_DIR=/run/user/%U"
        ];
        Restart = "on-failure";
      };
      Install.WantedBy = [ "avatar.target" ];
    };
    systemd.user.services.avatar-camera = {
      Unit = {
        Description = "Avatar virtual camera";
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
        ExecStart = toString camera;
        ExecStopPost = "${pkgs.python312}/bin/python3 ${browserRuntime} stop";
        Environment = [
          "PATH=${lib.makeBinPath [ pkgs.chromium ]}"
          "V4L2_DEVICE=/dev/video10"
        ];
        Restart = "on-failure";
      };
      Install.WantedBy = [ "avatar.target" ];
    };
    systemd.user.services.avatar-renderer = {
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
}
