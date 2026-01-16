---
description: NixOS dotfiles repository specific AI guidelines
alwaysApply: true
---

Do not change this file if not requested or if the change does not follow the pattern that focuses on token usage and information density. Follow these rules at all costs. These are repository-specific patterns that must be followed without exception.

NixOS Patterns
Use conditional configs with lib.mkIf for optional features. Check file existence with builtins.pathExists before including secrets. Import modules from nixos/modules/ following existing structure.

Agenix Secrets
Keep secrets in secrets/ directory encrypted with agenix. Each .age file gets entry in secrets.nix mapping to public keys that can decrypt. Use conditional configs to allow rebuilds without secret files so we don't break the system rebuild. Edit secrets with agenix-edit script. Public keys in secrets.nix are safe to commit. Private keys stay on machine only.

File Organization
Scripts in bin/ for executables. Home Manager scripts in home/scripts/. NixOS modules in nixos/modules/. User configs in users/<username>/. Secrets in secrets/ with secrets.nix defining access. Follow existing import patterns.

Scripts
Raw scripts go in bin/. Create <name>.nix in home/scripts/ or users/<username>/scripts/ following pattern in respective default.nix. Scripts requiring root use sudo wrapper or check EUID in script.

Common Tasks
Rebuild with ./bin/rebuild. Edit secrets with agenix-edit <secret-name>. Always check config with nix flake check. Add new module by creating in appropriate directory and importing in user config.

AI Workflow
Home-manager on non-NixOS systems does not require sudo. ALWAYS run `./bin/rebuild` after ANY nix config change to validate. ALWAYS test changes work as expected. ALWAYS commit if rebuild succeeds and changes are verified - do not ask for permission.

Private Files
Two systems: agenix for secrets (passwords, keys, tokens) in secrets/. git-crypt for private non-secret files (work agents, company skills) in private-config/. Files in private-config/ are encrypted in git, plaintext locally. Never mention the company named after the second letter of the greek alphabet with h between t and a - use generic names for that context only.
