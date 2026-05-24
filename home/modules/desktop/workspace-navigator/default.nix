{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "workspace-navigate" ''
      export PATH="${pkgs.aerospace}/bin:${pkgs.gawk}/bin:$PATH"
      exec ${pkgs.bash}/bin/bash ${./workspace-navigator.sh} "$@"
    '')
  ];
}
