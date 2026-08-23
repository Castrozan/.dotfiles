{ pkgs }:
let
  entryDelimiter = "\n§\n";

  userMemoryEntries = [
    "User identity: Lucas is a senior software engineer."
    "Writing preference: Lucas prefers English and avoids em dashes, en dashes, and hyphens used as sentence dashes while preserving normal hyphenated compounds."
  ];

  agentMemoryEntries = [
    "Machine configuration: Lucas's primary machine is a nix-darwin setup managed from ~/.dotfiles. Rebuild is sudoless through a command-scoped NOPASSWD rule, so a bare sudo probe can fail without implying rebuild needs a password."
    "Hermes configuration: Hermes is Nix-packaged through a wrapper and pinned uv environment at ~/.hermes/.venv. The wrapper regenerates config.yaml and SOUL.md from agent-harness/harnesses/hermes on every launch."
    "Inference configuration: Hermes uses the openai-codex provider with gpt-5.5 and keeps its own OAuth session in ~/.hermes/auth.json. Adopting ~/.codex/auth.json credentials is an explicit Hermes authentication action; it has no API key to manage."
    "Repository concurrency: Multiple agent sessions work in the dotfiles repository concurrently."
  ];

  retiredUserMemoryEntryPrefixes = [
    "Identity:"
    "Correction stance:"
    "Uncertainty:"
    "Writing mechanics:"
    "Interactive reply shape:"
    "Before returning control:"
    "Code style he enforces:"
    "Scripts:"
    "Git:"
  ];

  retiredAgentMemoryEntryPrefixes = [
    "Lucas's primary machine is a nix-darwin"
    "Hermes itself is nix-packaged here"
    "Inference uses the openai-codex provider"
    "Assume parallel work in the dotfiles repo"
  ];

  joinEntries = entries: builtins.concatStringsSep entryDelimiter entries;
  joinLines = lines: builtins.concatStringsSep "\n" lines;
in
{
  userMemory = pkgs.writeText "hermes-USER.md" (joinEntries userMemoryEntries);
  agentMemory = pkgs.writeText "hermes-MEMORY.md" (joinEntries agentMemoryEntries);
  retiredUserMemoryEntryPrefixes = pkgs.writeText "hermes-retired-user-memory-entry-prefixes" (
    joinLines retiredUserMemoryEntryPrefixes
  );
  retiredAgentMemoryEntryPrefixes = pkgs.writeText "hermes-retired-agent-memory-entry-prefixes" (
    joinLines retiredAgentMemoryEntryPrefixes
  );
}
