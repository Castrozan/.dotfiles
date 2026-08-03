{ pkgs }:
let
  pythonSource = pkgs.writeText "verify-deployed-prohibited-words-allowlist-source.py" (
    builtins.readFile ./verify_deployed_prohibited_words_allowlist.py
  );
in
pkgs.writeShellScriptBin "verify-deployed-prohibited-words-allowlist" ''
  export PATH=${pkgs.nix}/bin:$PATH
  exec ${pkgs.python312}/bin/python3 ${pythonSource} "$@"
''
