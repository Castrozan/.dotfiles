{
  pkgs,
  lib,
  programs,
  host,
  hostname,
}:
let
  scripts = ../scripts;
  controlServer = ../../../../agent-harness/agent-instructions/skills/workstation/avatar/scripts/control-server;
  speech = import ../../media-generation/speech-package.nix { inherit pkgs; };
  conversationPython = pkgs.python312.withPackages (
    packages: with packages; [
      numpy
      onnxruntime
      websockets
    ]
  );
  modules = lib.concatStringsSep ":" [
    "${scripts}/listening"
    "${scripts}/echo"
    "${scripts}/conversation"
    "${scripts}/conversation/remote_seat"
    "${scripts}/conversation/mac_conversation"
    "${scripts}/wake"
  ];
  environment = ''
    export AVATAR_HOST=${host}
    export AVATAR_AGENT_HOST=${hostname}
    export AVATAR_SEAT_PAGE=${scripts}/conversation/remote_seat/page
    export AVATAR_SERVANT_CHARACTERS=${programs.servantCharacters}
    export AVATAR_CHARACTER_VOICES=${import ../cast/character-voices.nix { inherit pkgs; }}
    export AVATAR_EMOTION_DELIVERY=${controlServer}/speech/emotion-delivery.json
    export AVATAR_TURN_MODEL=${import ./avatar-turn-model.nix { inherit pkgs; }}
    export AVATAR_ORDINARY_WORDS=${programs.ordinaryWords}
    export AVATAR_SERVANT_ROSTER=${../../../../agent-harness/servants/roster.txt}
    export PYTHONPATH=${modules}
  '';
in
{
  inherit modules;
  talk = pkgs.writeShellScriptBin "avatar-talk" ''
    export PATH=${lib.makeBinPath [ speech ]}:$PATH
    ${environment}
    exec ${conversationPython}/bin/python3 ${scripts}/conversation/mac_conversation/mac_talk.py "$@"
  '';
  listener = pkgs.writeShellScriptBin "avatar-conversation-listener" ''
    ${environment}
    exec ${conversationPython}/bin/python3 ${scripts}/listening/listener.py
  '';
}
