{ pkgs }:
{
  packages = [
    (pkgs.writeShellScriptBin "ci-watcher" ''
      export PATH="${pkgs.git}/bin:${pkgs.openssh}/bin:${pkgs.gh}/bin:${pkgs.glab}/bin:''${PATH:+:$PATH}"
      export PYTHONPATH="${../scripts}:${../../forge/scripts}''${PYTHONPATH:+:$PYTHONPATH}"
      exec ${pkgs.python312}/bin/python3 -m ci_watcher "$@"
    '')
  ];
}
