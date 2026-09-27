{
  pkgs,
  lib,
  hostname,
  isDarwin ? false,
  privateConfigRoot ? ../../../../private-configuration,
}:
let
  rulesync = import ../package.nix { inherit pkgs; };
  hookScripts = import ../../../hooks/flat-hook-scripts-directory.nix { inherit pkgs lib; };
  canonical = import ./source.nix {
    inherit
      pkgs
      lib
      hostname
      isDarwin
      privateConfigRoot
      ;
  };
  source = pkgs.writeText "rulesync-hooks.json" (builtins.toJSON canonical);
  runner = "${hookScripts}/run-hook.sh";
  opencodeRunner = "${runner} ${../../../hooks/integrations/opencode/policy-transport}/dispatch.py";
in
pkgs.runCommand "rulesync-native-hooks"
  {
    nativeBuildInputs = [ pkgs.python312 ];
    passthru = { inherit source canonical; };
  }
  ''
    python3 ${./build_hooks.py} ${source} "$out" \
      --rulesync ${rulesync}/bin/rulesync \
      --runner ${lib.escapeShellArg runner} \
      --opencode-runner ${lib.escapeShellArg opencodeRunner}
  ''
