{ pkgs, lib, ... }:
let
  sharedHooksDirectory = ../../../../agents/hooks;

  hookScriptRelativePaths = [
    "common/changed_file_paths.py"
    "common/codex_tool_payload.py"
    "post-tool-use/formatter_table_by_extension.py"
    "post-tool-use/auto-format.py"
    "post-tool-use/nix-rebuild-trigger.py"
    "lint/lint_ledger.py"
    "lint/linter_table_by_extension.py"
    "lint/repo_native_lint_command_detection.py"
    "lint/record-edited-source-file.py"
    "lint/lint-turn-review.py"
    "pre-tool-use/memory-recall/memory-recall.py"
    "pre-tool-use/memory-recall/memory_recall_debounce.py"
    "pre-tool-use/memory-recall/memory_recall_io.py"
    "pre-tool-use/memory-recall/memory_recall_keywords.py"
    "pre-tool-use/memory-recall/memory_recall_memory_directory.py"
    "pre-tool-use/memory-recall/memory_recall_ripgrep.py"
    "pre-tool-use/prohibited-command-guard/prohibited-command-guard.py"
    "pre-tool-use/prohibited-words-guard/prohibited-words-guard.py"
  ];

  installHookScriptCommand =
    relativePath:
    let
      hookScriptSource = sharedHooksDirectory + "/${relativePath}";
      deployedFilename = builtins.baseNameOf relativePath;
    in
    ''install -m 0644 ${hookScriptSource} "$out/${deployedFilename}"'';
in
pkgs.runCommandLocal "codex-hook-scripts" { } ''
  mkdir -p "$out"
  ${lib.concatMapStringsSep "\n" installHookScriptCommand hookScriptRelativePaths}
''
