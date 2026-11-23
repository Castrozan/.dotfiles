{
  pkgs,
  herdrPackage,
}:
let
  selectorSources = pkgs.runCommand "herdr-client-selector-sources" { } ''
    mkdir -p "$out/scripts/herdr_client"
    cp ${./scripts/select-herdr-client.py} "$out/scripts/select-herdr-client.py"
    cp ${./scripts/herdr_client/selection.py} "$out/scripts/herdr_client/selection.py"
    cp ${./scripts/herdr_client/running_server_record.py} "$out/scripts/herdr_client/running_server_record.py"
  '';
  selector = pkgs.writeShellApplication {
    name = "select-herdr-client";
    runtimeInputs = [
      pkgs.lsof
      pkgs.nix
      pkgs.python3
    ];
    text = ''
      exec python3 ${selectorSources}/scripts/select-herdr-client.py "$@"
    '';
  };
  package = pkgs.writeShellApplication {
    name = "herdr";
    runtimeInputs = [ selector ];
    text = ''
      set -- ${herdrPackage}/bin/herdr "$@"
      ${builtins.readFile ./scripts/run-herdr-client.sh}
    '';
  };
in
{
  inherit package selector;
}
