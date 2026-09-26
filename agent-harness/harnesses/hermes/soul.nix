{ pkgs }:
let
  hermesIdentity = "You are Hermes Agent, an intelligent AI assistant created by Nous Research.";
  canonicalCore = "${
    import ../../agent-instructions/rulesync { inherit pkgs; }
  }/hermesagent/.hermes.md";
  identity = pkgs.writeText "hermes-identity.md" "### Harness identity\n\n${hermesIdentity}\n\n";
in
pkgs.runCommand "hermes-SOUL.md" { } ''
  cat ${identity} ${canonicalCore} > "$out"
''
