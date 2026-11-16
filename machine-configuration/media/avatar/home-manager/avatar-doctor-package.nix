{
  pkgs,
  lib,
  commands,
  arguments,
}:
pkgs.writeShellScriptBin "avatar-doctor" ''
  export PATH=${lib.makeBinPath commands}:$PATH
  exec ${pkgs.python312}/bin/python3 ${../scripts/doctor}/doctor.py ${arguments} "$@"
''
