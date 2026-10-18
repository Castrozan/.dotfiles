{
  pkgs,
  lib,
  ...
}:
let
  chatgpt = pkgs.callPackage ../package.nix { };
in
lib.optionalAttrs pkgs.stdenv.hostPlatform.isLinux {
  domain-chatgpt-wrapper-finds-bubblewrap =
    pkgs.runCommand "check-chatgpt-wrapper-finds-bubblewrap"
      {
        nativeBuildInputs = [ pkgs.makeWrapper ];
      }
      ''
        makeWrapper ${pkgs.runtimeShell} "$TMPDIR/chatgpt-shell" ${lib.escapeShellArgs chatgpt.gappsWrapperArgs}
        PATH= "$TMPDIR/chatgpt-shell" -c \
          ${lib.escapeShellArg ''test "$(command -v bwrap)" = "${lib.getExe pkgs.bubblewrap}"''}
        touch "$out"
      '';
}
