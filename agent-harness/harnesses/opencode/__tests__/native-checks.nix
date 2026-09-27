{
  pkgs,
  lib,
  cfg,
}:
let
  generatedInstructions = import ../../../agent-instructions/rulesync { inherit pkgs; };
  rulesync = import ../../../agent-instructions/rulesync/package.nix { inherit pkgs; };
  evaluationRuntime =
    pkgs.callPackage ../../../quality/evaluations/node-provider-runtime/package.nix
      {
        nodejs = pkgs.nodejs_22;
      };

in
{
  domain-opencode-native-cli-configuration =
    pkgs.runCommand "domain-opencode-native-cli-configuration" { }
      ''
        export PYTHONPATH=${./.}:${../../../agent-instructions/rulesync/__tests__}
        ${pkgs.python312}/bin/python3 ${./.}/verify-native-cli-configuration.py \
          ${cfg.opencode.unwrappedPackage}/bin/opencode \
          ${cfg.home.file.".config/opencode/cli.json".source} \
          ${generatedInstructions}/opencode/.opencode/agents
        touch "$out"
      '';

  domain-opencode-native-plugin-configuration =
    pkgs.runCommand "domain-opencode-native-plugin-configuration" { }
      ''
        ${pkgs.python312}/bin/python3 ${./.}/verify-native-plugin-configuration.py \
          ${cfg.opencode.unwrappedPackage}/bin/opencode \
          ${cfg.home.file.".config/opencode/opencode.json".source} \
          ${cfg.home.file.".config/opencode/opencode.jsonc".source} \
          ${cfg.agentPlugins.bundle} ${lib.escapeShellArg cfg.agentPlugins.opencodeDataRoot}
        touch "$out"
      '';

  domain-opencode-native-hooks =
    pkgs.runCommand "domain-opencode-native-hooks"
      {
        nativeBuildInputs = [ pkgs.python312 ];
      }
      ''
        export PYTHONPATH=${./.}:${../../../agent-instructions/rulesync/__tests__}
        python3 ${../../../hooks/integrations/opencode}/__tests__/verify-native-hook-bridge.py \
          ${cfg.opencode.unwrappedPackage}/bin/opencode ${generatedInstructions}/opencode/.opencode/agents ${rulesync}/bin/rulesync
        touch "$out"
      '';

  domain-opencode-native-evaluation-runtime =
    pkgs.runCommand "domain-opencode-native-evaluation-runtime"
      {
        nativeBuildInputs = [
          pkgs.python312
          pkgs.nodejs_22
        ];
      }
      ''
        export PYTHONPATH=${./.}:${../../../agent-instructions/rulesync/__tests__}
        python3 ${./.}/verify-native-evaluation-runtime.py \
          ${cfg.opencode.unwrappedPackage}/bin/opencode \
          ${evaluationRuntime}/lib/node_modules/agent-eval-node-provider-runtime/provider-runtime.mjs \
          ${generatedInstructions}/opencode/.opencode/agents
        touch "$out"
      '';

}
