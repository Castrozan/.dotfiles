{ pkgs, skillDirectory }:
let
  workflow = pkgs.concatText "research-pulse.workflow.js" [
    ./schemas.js
    ./source-prompts.js
    ../research-pulse.workflow.js
  ];
in
pkgs.runCommand "research-instruction-skill" { } ''
  cp -R ${skillDirectory} "$out"
  chmod u+w "$out" "$out/research-pulse.workflow.js"
  cp ${workflow} "$out/research-pulse.workflow.js"
''
