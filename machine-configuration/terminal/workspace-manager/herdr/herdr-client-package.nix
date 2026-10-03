{
  pkgs,
  herdrPackage,
}:
let
  selectorSources = pkgs.runCommand "herdr-client-selector-sources" { } ''
    mkdir -p "$out/scripts/herdr_client"
    cp ${./scripts/select-herdr-client.py} "$out/scripts/select-herdr-client.py"
    cp ${./scripts/herdr_client/selection.py} "$out/scripts/herdr_client/selection.py"
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
      selected_executable="$(select-herdr-client select ${herdrPackage}/bin/herdr "$@")"
      exec "$selected_executable" "$@"
    '';
  };
in
{
  inherit package selector;
}
