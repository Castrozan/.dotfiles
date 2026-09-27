{
  pkgs,
  lib,
  hostname,
  isDarwin,
}:
let
  configuration = import ../rulesync { inherit pkgs; };
  hooks = import ../rulesync/hooks {
    inherit
      pkgs
      lib
      hostname
      isDarwin
      ;
  };
  sources = pkgs.runCommand "rulesync-complete-sources" { } ''
    mkdir -p "$out"
    cp -r ${configuration.sources}/* "$out/"
    cp ${hooks.source} "$out/hooks.json"
  '';
in
[
  {
    name = "agents";
    path = "${configuration}/claudecode/.claude/agents";
  }
  {
    name = "configuration/rulesync";
    path = sources;
  }
  {
    name = "native/claude/CLAUDE.md";
    path = "${configuration}/claudecode/CLAUDE.md";
  }
  {
    name = "native/codex/AGENTS.md";
    path = "${configuration}/codexcli/AGENTS.md";
  }
  {
    name = "native/opencode/AGENTS.md";
    path = "${configuration}/opencode/AGENTS.md";
  }
  {
    name = "native/hermes/.hermes.md";
    path = "${configuration}/hermesagent/.hermes.md";
  }
  {
    name = "native/opencode/hooks";
    path = "${hooks}/opencode/.opencode/plugins/rulesync-hooks.js";
  }
  {
    name = "native/claude/hooks.json";
    path = "${hooks}/claudecode/.claude/settings.json";
  }
  {
    name = "native/codex/hooks.json";
    path = "${hooks}/codexcli/.codex/hooks.json";
  }
  {
    name = "native/opencode/agents";
    path = "${configuration}/opencode/.opencode/agents";
  }
]
