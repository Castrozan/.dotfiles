{
  pkgs,
  lib,
  herdr,
  unclaimedCommand,
  servantCharacters,
  a2aLibrary,
}:
pkgs.writeShellScriptBin "avatar-claim-floor" ''
  export PATH=${
    lib.makeBinPath (
      [
        herdr
        unclaimedCommand
      ]
      ++ lib.optionals pkgs.stdenv.hostPlatform.isLinux [
        pkgs.openssh
        pkgs.systemd
      ]
    )
  }:$PATH
  export AVATAR_SERVANT_CHARACTERS=${servantCharacters}
  export PYTHONPATH=${../scripts/listening}:${../scripts/echo}:${../scripts/wake}:${a2aLibrary}
  exec ${pkgs.python312}/bin/python3 ${../scripts/wake}/floor_cli.py "$@"
''
