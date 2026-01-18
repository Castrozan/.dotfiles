---
description: Devenv usage patterns for AI agents managing development environments
alwaysApply: false
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<entering>
devenv shell activates all packages, environment variables, runs enterShell commands. Shell stays active until exit. Use for interactive work.
</entering>

<single_commands>
devenv shell -- command runs command in devenv then returns to normal shell. Preferred for CI/scripts or one-off commands. Example: devenv shell -- yarn install
</single_commands>

<updating>
devenv update updates devenv.lock. WARNING: newer versions may introduce bugs. Only update when necessary. If update breaks: restore previous lock from git or copy working lock from another project.
</updating>

<cleaning>
When devenv behaves strangely or builds fail unexpectedly: rm -rf .devenv/ .devenv.flake.nix removes cached state. Run devenv shell again to rebuild.
</cleaning>

<options>
packages = [ pkgs.nodejs ] - system packages | env.VAR = "value" - environment variables | enterShell = "echo Hello" - shell entry commands | scripts.name.exec = "command" - custom scripts | cachix.enable = false - disable if issues | languages.javascript.enable = true - language tooling
</options>

<lock_copying>
When devenv version causes issues: cp /path/to/working/project/devenv.lock ./devenv.lock. Pins exact versions. Ensure source project is compatible. After copying: devenv shell to verify.
</lock_copying>

<direnv>
DO NOT USE direnv. Unreliable, causes more issues than it solves. Always use devenv shell or devenv shell -- command directly.
</direnv>

<troubleshooting>
1. Check error message (secretspec, hash errors, package not found)
2. Clean cache: rm -rf .devenv/ .devenv.flake.nix
3. If version-related: copy working lock file
4. Verify syntax: nix flake check or attempt devenv shell
5. Check version: devenv version

Common errors: "command not found" after entering shell - package not in list or PATH issue. Direnv not loading - run direnv allow.
</troubleshooting>
