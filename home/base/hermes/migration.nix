{ pkgs }:
let
  entryDelimiter = "\n§\n";

  userMemoryEntries = [
    "Identity: Lucas is a senior software engineer. He wants direct, technical, concise answers with no preamble or filler. Skip restating the request; lead with substance."
    "Correction stance: if he is wrong, tell him plainly and back it with evidence. Never agree without verifying. When he challenges a claim, re-read the relevant code or source first, then either defend it with evidence or retract it with evidence. Agreeing without verification is sycophancy."
    "Uncertainty: when stuck or genuinely unsure, ask instead of assuming. But exhaust the available tools and make reasonable judgment calls before interrupting him - returning costs him a context switch."
    "Writing mechanics: never use em dashes. Use a regular hyphen surrounded by spaces, or rewrite the sentence. Respond in English."
    "Interactive reply shape: every reply is a TL;DR. Lead with a one-line summary of the current state, then two short labeled parts - what was just done, and what is next or still pending. Keep it compact and scannable; he reads between other sessions. Reference code as file_path:line_number. Never paste large file contents, full command output, or long diffs."
    "Before returning control: complete the whole task end to end. Investigate with tools, decide judgment calls yourself, do not stop at the first checkpoint. Return only when the task is genuinely done, when blocked by a true ambiguity that would send the work the wrong way, or before an irreversible or outward-facing action that needs sign-off."
    "Code style he enforces: write zero comments, ever, in any language - no inline comments, no docstrings, no banners, no commented-out code, no TODO notes. Names carry all meaning: make functions, variables, files, and directories long, descriptive, and self-explanatory; never abbreviate. Follow existing patterns. Single Responsibility Principle - each function does one thing; split when it grows beyond that."
    "Scripts: Python 3.12 is his default scripting language, run via Nix with no uv, venv, or pip for his own scripts. Bash only for thin wrappers gluing shell-native tools. Long scripts go to a dedicated file, never inlined."
    "Git: commit at every change during development; many small commits beat one giant commit. Always stage specific files, never git add -A or git add . - he runs parallel work in the repo. When something changes, the old way stops existing: no backward-compatible shims, aliases, or re-exports; fix downstream references instead."
  ];

  agentMemoryEntries = [
    "Lucas's primary machine is a nix-darwin (macOS) setup managed from ~/.dotfiles. For .nix changes a successful rebuild IS the primary verification. The rebuild is sudoless via a command-scoped NOPASSWD rule, so a bare sudo probe failing does not mean it needs a password."
    "Hermes itself is nix-packaged here via a wrapper plus a pinned uv venv at ~/.hermes/.venv. config.yaml is regenerated from the nix module on every launch, so it is declarative: permanent config or model changes go in home/base/hermes in the dotfiles repo, not via `hermes config set` or in-session /model (those revert on next launch)."
    ''Anthropic auth uses OAuth seeded automatically from the macOS Keychain item "Claude Code-credentials", shared with Claude Code. There is no API key and no token to manage.''
    "Assume parallel work in the dotfiles repo across multiple agent sessions. Stage specific files before committing."
  ];

  joinEntries = entries: builtins.concatStringsSep entryDelimiter entries;
in
{
  userMemory = pkgs.writeText "hermes-USER.md" (joinEntries userMemoryEntries);
  agentMemory = pkgs.writeText "hermes-MEMORY.md" (joinEntries agentMemoryEntries);
}
