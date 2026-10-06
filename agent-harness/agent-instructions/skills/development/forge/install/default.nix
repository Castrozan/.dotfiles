{ pkgs }:
{
  packages = [
    (pkgs.writeShellScriptBin "git-forge" ''
      export PATH="${pkgs.git}/bin:${pkgs.openssh}/bin:${pkgs.gh}/bin:${pkgs.glab}/bin:''${PATH:+:$PATH}"
      exec ${pkgs.python312}/bin/python3 ${../scripts}/forge_cli.py "$@"
    '')
  ];
}
