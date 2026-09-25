{ pkgs, ... }:
let
  distribution = import ../. { inherit pkgs; };
  fixture = ./fixtures/portable-plugin;
  bundle = distribution.buildPlugin {
    source = fixture;
    opencodeDataRoot = "/tmp/agent-plugin-distribution-state";
  };
in
{
  agent-plugin-distribution =
    pkgs.runCommand "check-agent-plugin-distribution"
      {
        nativeBuildInputs = [
          pkgs.python312
          distribution.package
        ];
      }
      ''
        python ${./verify_plugin_bundle.py} ${bundle} ${fixture}
        python ${./verify_build_contract.py} ${fixture}
        touch "$out"
      '';
}
