{ pkgs, stackRoot }:
pkgs.writeShellScriptBin "arr-media" ''
  export ARR_MEDIA_STACK_HOME=${pkgs.lib.escapeShellArg stackRoot}
  exec ${pkgs.python312}/bin/python3 ${./scripts/arr_media}/__main__.py "$@"
''
