{ pkgs, lib }:
pkgs.writeShellApplication {
  name = "hex-dictation-notifier";
  runtimeInputs = [
    pkgs.coreutils
  ]
  ++ lib.optionals pkgs.stdenv.isLinux [
    pkgs.libnotify
    pkgs.systemd
  ]
  ++ lib.optionals pkgs.stdenv.isDarwin [ pkgs.terminal-notifier ];
  text = ''
    exec ${pkgs.python312}/bin/python3 -P ${./scripts/hex_dictation_notifier.py} "$@"
  '';
}
