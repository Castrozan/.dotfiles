{
  pkgs,
  lib,
  programs,
  host,
  hostname,
}:
let
  scripts = ../scripts;
  characters = import ../cast/characters.nix { inherit pkgs; };
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
    "${scripts}/wake/mac"
  ];
  environment = ''
    export AVATAR_HOST=${host}
    export AVATAR_AGENT_HOST=${hostname}
    export AVATAR_SEAT_PAGE=${scripts}/conversation/remote_seat/page
    export AVATAR_SERVANT_CHARACTERS=${programs.servantCharacters}
    export AVATAR_TURN_MODEL=${import ./avatar-turn-model.nix { inherit pkgs; }}
    export AVATAR_ORDINARY_WORDS=${programs.ordinaryWords}
    export AVATAR_SERVANT_ROSTER=${../../../../agent-harness/servants/roster.txt}
    export PYTHONPATH=${modules}
  '';
  seatPlay = pkgs.writeShellScriptBin "avatar-seat-play" ''
    ${environment}
    exec ${conversationPython}/bin/python3 ${scripts}/conversation/mac_conversation/mac_seat_play.py "$@"
  '';
  floor = pkgs.writeShellScriptBin "avatar-claim-floor" ''
    export PATH=${
      lib.makeBinPath [
        programs.herdr
        programs.unclaimedCommand
      ]
    }:$PATH
    export AVATAR_SERVANT_CHARACTERS=${programs.servantCharacters}
    export PYTHONPATH=${scripts}/listening:${scripts}/echo:${scripts}/wake:${programs.a2aLibrary}
    exec ${pkgs.python312}/bin/python3 ${scripts}/wake/floor_cli.py "$@"
  '';
in
{
  inherit modules;
  command = programs.unclaimedCommand;
  controlServer = pkgs.writeShellScriptBin "avatar-control-server" ''
    export PATH=${
      lib.makeBinPath [
        speech
        seatPlay
      ]
    }:$PATH
    export AVATAR_CLOUD_VOICE=${(builtins.head characters).cloudVoice}
    export AVATAR_CHARACTER_VOICES=${import ../cast/character-voices.nix { inherit pkgs; }}
    exec ${pkgs.nodejs_22}/bin/node ${programs.control}/server.js
  '';
  renderer = pkgs.writeShellScriptBin "avatar-renderer-server" ''
    exec ${programs.serve}
  '';
  talk = pkgs.writeShellScriptBin "avatar-talk" ''
    export PATH=${
      lib.makeBinPath [
        programs.unclaimedCommand
        floor
      ]
    }:$PATH
    ${environment}
    export PYTHONPATH=$PYTHONPATH:${scripts}
    exec ${conversationPython}/bin/python3 ${scripts}/conversation/mac_conversation/mac_talk.py "$@"
  '';
  listener = pkgs.writeShellScriptBin "avatar-conversation-listener" ''
    ${environment}
    exec ${conversationPython}/bin/python3 ${scripts}/listening/listener.py
  '';
  live = pkgs.writeShellScriptBin "avatar-live" ''
    export PATH=${
      lib.makeBinPath [
        programs.a2a
        programs.herdr
      ]
    }:$PATH
    ${environment}
    export AVATAR_CHARACTER_VOICES=${import ../cast/character-voices.nix { inherit pkgs; }}
    export PYTHONPATH=${scripts}/live:$PYTHONPATH
    exec ${conversationPython}/bin/python3 ${scripts}/live/live_bridge.py
  '';
}
