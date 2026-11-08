{
  pkgs,
  forgePythonPath,
  machineName,
}:
let
  runtimePath = pkgs.lib.makeBinPath [
    pkgs.curl
    pkgs.gh
    pkgs.git
    pkgs.glab
    pkgs.openssh
    pkgs.yt-dlp
  ];
in
pkgs.writeShellScriptBin "ril" ''
  export PATH="${runtimePath}''${PATH:+:$PATH}"
  export PYTHONPATH="${forgePythonPath}''${PYTHONPATH:+:$PYTHONPATH}"
  export RIL_MACHINE_NAME="${machineName}"
  exec ${pkgs.python312}/bin/python ${./ril_cli}/ril.py "$@"
''
