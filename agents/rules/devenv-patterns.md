---
description: Devenv usage patterns for AI agents managing development environments
alwaysApply: false
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

Entering Environment
Enter development shell with `devenv shell`. This activates all packages, environment variables, and runs enterShell commands. Shell stays active until exit. Use when you need interactive work in the environment.

Running Single Commands
Run command in devenv without entering shell with `devenv shell -- command`. Example: `devenv shell -- yarn install`. The command runs in the environment then returns to normal shell. Preferred for CI/scripts or one-off commands.

Updating Dependencies
Update devenv.lock with `devenv update`. WARNING: Newer versions may introduce bugs. Only update when necessary. If update breaks things, restore previous lock file from git or copy working lock from another project.

Cleaning Cache
When devenv behaves strangely or builds fail unexpectedly, clean cache with `rm -rf .devenv/ .devenv.flake.nix`. This removes all cached state. Run `devenv shell` again to rebuild from scratch.

Key devenv.nix Options
- `packages = [ pkgs.nodejs pkgs.yarn ]` - System packages to include in environment
- `env.VAR = "value"` - Set environment variables. Example: `env.NODE_OPTIONS = "--openssl-legacy-provider"`
- `enterShell = "echo Hello"` - Commands run when entering shell
- `scripts.name.exec = "command"` - Custom scripts available as commands
- `cachix.enable = false` - Disable cachix if it causes issues
- `languages.javascript.enable = true` - Enable language-specific tooling

Copying Lock Files
When devenv version causes issues, copy working devenv.lock from another repo: `cp /path/to/working/project/devenv.lock ./devenv.lock`. This pins exact versions. Ensure source project is compatible (same devenv.nix patterns). After copying, run `devenv shell` to verify.

Direnv Integration
DO NOT USE direnv. It's unreliable and causes more issues than it solves. Always use `devenv shell` or `devenv shell -- command` directly.

Troubleshooting Workflow
1. Check error message for clues (secretspec, hash errors, package not found)
2. Try cleaning cache: `rm -rf .devenv/ .devenv.flake.nix`
3. If version-related, copy working lock file from compatible project
4. Verify devenv.nix syntax: `nix flake check` or just attempt `devenv shell`
5. Check devenv version: `devenv version`

Common Errors
- "command not found" after entering shell - Package not in packages list or PATH issue
- Direnv not loading - Run `direnv allow`
