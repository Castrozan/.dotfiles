{
  pkgs,
  lib,
  isNixOS,
  ...
}:
let
  programs = import ./avatar-programs.nix { inherit pkgs lib; };
  characters = import ./characters.nix { inherit pkgs; };
  characterVoices = pkgs.writeText "avatar-character-voices.json" (
    builtins.toJSON (map (character: { inherit (character) name cloudVoice localVoice; }) characters)
  );
  transcriptionModel = pkgs.fetchurl {
    url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small-q5_1.bin";
    sha256 = "1fqi0h90ig4ifpyb44cfc7dmnndv2vy5mr9g22yng9fp6nly91df";
  };
  speechVoices = import ./speech-voices.nix { inherit pkgs; };
  tools = lib.makeBinPath [
    programs.audio
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
    home.packages = with programs; [
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
            ExecStart = "${programs.audio}/bin/avatar-audio start";
            ExecStop = "${programs.audio}/bin/avatar-audio stop";
          };
        };
        avatar-control-server = {
          Unit = serviceUnit // {
            Description = "Avatar control server";
          };
          Service = {
            ExecStart = "${pkgs.nodejs_22}/bin/node ${programs.control}/server.js";
            Environment = [
              "PATH=${tools}"
              "AVATAR_CLOUD_VOICE=${(builtins.head characters).cloudVoice}"
              "AVATAR_CHARACTER_VOICES=${characterVoices}"
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
            ExecStart = "${pkgs.python312}/bin/python3 ${programs.browserRuntime} supervise http://localhost:3000/?output=1";
            ExecStopPost = "${pkgs.python312}/bin/python3 ${programs.browserRuntime} stop";
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
            ExecStart = toString programs.camera;
            Environment = [ "V4L2_DEVICE=/dev/video10" ];
            Restart = "always";
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
            After = [ "hex.service" ];
            Wants = [ "hex.service" ];
          };
          Service = {
            ExecStart = toString programs.listener;
            Restart = "on-failure";
          };
        };
        avatar-renderer = {
          Unit = serviceUnit // {
            Description = "Offline avatar renderer";
          };
          Service = {
            ExecStart = toString programs.serve;
            Restart = "on-failure";
          };
          Install.WantedBy = [ "avatar.target" ];
        };
      };
    };
  };
}
