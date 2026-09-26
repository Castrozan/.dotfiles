{ pkgs, ... }:
let
  configuration = import ../. { inherit pkgs; };
  rulesync = import ../package.nix { inherit pkgs; };
  pythonEnvironment = pkgs.python312.withPackages (packages: [ packages.pyyaml ]);
  opencode = import ../../../harnesses/opencode/upstream-package.nix { inherit pkgs; };
in
{
  rulesync-configuration-contract = pkgs.runCommand "rulesync-configuration-contract" { } ''
    ${pythonEnvironment}/bin/python3 ${./verify-configuration.py} \
      --configuration ${configuration} \
      --source ${configuration.sources} \
      --rulesync ${rulesync}/bin/rulesync \
      --builder ${../scripts/build_configuration.py} \
      --core-instructions ${../../core-rules/core.md}
    touch "$out"
  '';

  rulesync-native-opencode-agents = pkgs.runCommand "rulesync-native-opencode-agents" { } ''
    ${pythonEnvironment}/bin/python3 ${./.}/verify-native-opencode-agents.py \
      ${opencode}/bin/opencode ${configuration}
    touch "$out"
  '';
}
