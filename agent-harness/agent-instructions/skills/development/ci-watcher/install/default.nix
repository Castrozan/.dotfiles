{ pkgs }:
{
  packages = [
    (pkgs.writeShellScriptBin "ci-watcher" ''
      export PATH="${pkgs.gh}/bin:''${PATH:+:$PATH}"
      exec ${pkgs.python312}/bin/python3 ${../scripts/ci_watcher.py} "$@"
    '')
  ];
}
