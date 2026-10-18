{ pkgs }:
let
  python = pkgs.python312.withPackages (packages: [ packages.markdown-it-py ]);
  sources = pkgs.writeText "wellput-plugin-sources.json" (
    builtins.toJSON {
      skill = ../skills/writing/humanize;
      core = ../core-rules/core.md;
      docs = ../skills/writing/docs/SKILL.md;
      rules = ../../hooks/runtime/common/human_facing_reply;
      guard = ../../hooks/runtime/stop/end_of_turn_format_guard_handler.py;
      renderer = ../../quality/evaluations/instructions/reply_format_instructions.py;
      tests = ../../hooks/runtime/__tests__/unit/replies;
      support = ../../hooks/runtime/__tests__/support/human_facing_reply_test_support.py;
      assets = ./assets;
      portableTests = ./__tests__/portable;
    }
  );
in
pkgs.runCommand "wellput-plugin"
  {
    nativeBuildInputs = [ python ];
    PYTHONDONTWRITEBYTECODE = "1";
  }
  ''
    python ${./scripts/export_plugin.py} ${sources} "$out"
    python -S ${./__tests__/portable/verify_plugin.py} "$out"
  ''
