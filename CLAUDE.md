# Claude Code Project Context

This is a NixOS dotfiles repository managed with Home Manager and Flakes.

## Important Files
- `./bin/rebuild` - Main rebuild script
- `./secrets/` - Agenix encrypted secrets
- `./users/zanoni/` - User-specific configuration
- `./home/modules/` - Home Manager modules

## Key Patterns
- Always use lib.mkIf for conditional configs
- Check file existence with builtins.pathExists
- Use agenix for secrets management
- Follow existing module structure

## User Preferences
- Direct and technical communication
- Implement first, explain if needed
- Test changes before presenting
- Fix build errors immediately