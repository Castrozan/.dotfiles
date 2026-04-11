# docker-manager Skill

Safe Docker container, image, volume, and network management with AI agents.

## Quick Start

```bash
# Invoke from any agent
docker-manager list
docker-manager inspect my-container
docker-manager logs my-app --tail=50 --follow
docker-manager stop my-app
docker-manager remove my-app --remove-volumes
docker-manager build . --tag myapp:v1
```

See `scripts/docker-manager --help` for full command reference.

## Files

- **SKILL.md** - Skill definition, safety boundaries, Docker traps and constraints
- **scripts/docker-manager** - Executable script with safe Docker operations
- **PROMPTS.md** - Agent guidance on how to use the skill correctly
- **README.md** - This file

## What This Solves

Raw `docker` CLI exposes dangerous foot-guns:
- `docker rm` succeeds on stopped containers; `docker rmi` then fails because image is still referenced
- Removing a container doesn't delete its data; orphaned volumes accumulate
- `docker exec` silently fails on stopped containers
- Logs may be truncated depending on log driver
- Container "running" doesn't mean "ready" — no built-in wait for healthchecks

**This script handles all of that.** Agents use the curated interface and operations are safe by default.

## Design Philosophy

1. **Script as authoritative interface** - `docker-manager` is the only way agents interact with Docker
2. **Safety by default** - Operations warn before data loss, fail cleanly on invalid states
3. **Ordered operations** - Stop before remove, remove containers before images, etc.
4. **State validation** - Check preconditions (container running for exec, no references for image removal)
5. **No surprises** - Errors are clear, timeouts have defaults, operations are idempotent where safe

## Integration with Dotfiles

This skill is deployed to all agents via home-manager:

```nix
# agents/default.nix (when configured)
environment.systemPackages = [
  ./skills/docker-manager/scripts/docker-manager
];
```

Agents access it as:
```bash
docker-manager <command>
```

## Common Workflows

See **PROMPTS.md** for detailed patterns:
- Container lifecycle (start, stop, remove with cleanup)
- Debugging (logs, exec, healthcheck)
- Image management (build, push, cleanup)
- Volume safety (backup before delete, orphan detection)

## Constraints

- **Script manages existing containers** — For creating new containers from scratch, use `docker run` or docker-compose directly
- **Single-container operations** — For multi-container apps, use docker-compose (this script complements it)
- **Requires Docker daemon running** — Script fails cleanly if daemon is down
- **Permissions** — User must have docker socket access (group membership or rootless setup)

## Architecture

```
docker-manager/
├── SKILL.md              # What agents must know (traps, constraints)
├── scripts/
│   └── docker-manager    # Safe command wrapper
├── PROMPTS.md            # How to use it correctly
└── README.md             # This file
```

The skill definition (SKILL.md) teaches agents about Docker's non-obvious behavior:
- Container states and readiness
- Volume persistence across removal
- Image dependencies and orphaning
- Network isolation modes
- Log driver behavior and truncation
- Registry authentication context

The prompts (PROMPTS.md) teach agents how to apply this knowledge:
- Always validate state before operations
- Always wait for readiness, not just running state
- Always backup before data deletion
- Always clean up orphaned resources

The script itself is the implementation — agents don't need to understand it, they just use it and trust it to be safe.

## Testing

Quick validation:

```bash
# Verify daemon
docker-manager validate

# List containers
docker-manager list

# Build example
docker-manager build . --tag test:latest

# Cleanup
docker-manager cleanup-images --dry-run
```

## Future Enhancements

- [ ] Compose integration (start/stop services)
- [ ] Resource limits validation (warn before OOM)
- [ ] Registry mirror config
- [ ] Log rotation policies
- [ ] Event hooks (run action on container state change)
