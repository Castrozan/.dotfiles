{ pkgs, ... }:
let
  nixGcPythonSource = pkgs.writeText "nix-gc-source.py" (builtins.readFile ./scripts/nix_gc.py);
in
{
  home.packages = [
    (pkgs.writeShellScriptBin "rebuild" (builtins.readFile ./scripts/rebuild))
    (pkgs.writeShellScriptBin "nix-gc" ''
      exec ${pkgs.python312}/bin/python3 ${nixGcPythonSource} "$@"
    '')
    (pkgs.writeShellScriptBin "tar-unzip2dir" (builtins.readFile ./scripts/tar-unzip2dir))
    (pkgs.writeShellScriptBin "mouse-poll-rate" ''
      export PATH="${pkgs.python3}/bin:$PATH"
      ${builtins.readFile ./scripts/mouse-poll-rate}
    '')
  ];
}
