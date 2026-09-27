{
  pkgs,
  lib,
  inputs,
  ...
}:
let
  integrationAssets = inputs.herdr + "/src/integration/assets/opencode";
  terminalPlugin = pkgs.runCommand "herdr-opencode-terminal-plugin" { } ''
    mkdir -p "$out"
    cp ${integrationAssets}/herdr-tui-session.js "$out/tui.js"
  '';
in
{
  home.file.".config/opencode/herdr-session".source = terminalPlugin;
  home.activation.retireHerdrOpenCodeInstallerAssets =
    lib.hm.dag.entryBetween [ "linkGeneration" ] [ "writeBoundary" ]
      ''
        legacyPlugin="$HOME/.config/opencode/plugins/herdr-agent-state.js"
        if cmp -s "$legacyPlugin" ${integrationAssets}/herdr-agent-state.js; then
          run rm "$legacyPlugin"
        fi
      '';
}
